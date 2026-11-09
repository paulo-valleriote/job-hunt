#!/usr/bin/env python3
"""Apoio ao comando /curriculo (básico): idioma, pasta de saída, coverage e PDF.

  curriculo.py idioma <texto da vaga> [--forcar en|pt]   -> imprime en|pt
  curriculo.py pasta --empresa E --cargo C [--base private/curriculos] [--data AAAA-MM-DD] -> imprime o caminho
  curriculo.py lint <pasta> --idioma en|pt               -> avisos de idioma e voz (exit 0 sempre)
  curriculo.py coverage <coverage_review.md>             -> valida o relatório
  curriculo.py pdf <pasta>                               -> resume.json -> .tex -> PDF

Heurística de idioma: conta stopwords EN vs PT no texto da vaga; empate cai em EN
(foco do usuário). O modelo só decide se o texto for ambíguo/misto (ver /curriculo).
"""
import argparse, json, re, shutil, subprocess, sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from triagem import _slug, _secao  # noqa: E402

BASE = ROOT / "private/curriculos"
VENDOR = ROOT / "vendor/meu-emprego-novo"
UP_SCRIPTS = "meu-emprego-novo-pipeline/scripts"
EN = set("the and with for you our are will team experience work of to in a an is we".split())
PT = set("o a os as e com para você nosso nossa são será time equipe experiência de do da em um uma é nós que não".split())


def detectar_idioma(texto, forcar=None):
    if forcar:
        if forcar not in ("en", "pt"):
            raise ValueError("idioma deve ser en ou pt")
        return forcar
    palavras = re.findall(r"[a-záàâãéêíóôõúç]+", texto.lower())
    en = sum(w in EN for w in palavras)
    pt = sum(w in PT for w in palavras)
    return "pt" if pt > en else "en"


VOZ_3P_EN = set("leads manages develops builds creates designs implements delivers improves reduces "
                "increases owns drives runs supports coordinates migrates automates oversees".split())


def _palavras(texto):
    """Palavras que contam para o idioma: sem siglas (tudo maiúsculo) nem números."""
    return [w for w in re.findall(r"[A-Za-zÀ-ÿ]+", texto)
            if not (w.isupper() and len(w) > 1)]


def _destoa(texto, idioma):
    """True se o texto tem mais palavras exclusivas do outro idioma do que do escolhido."""
    ps = [w.lower() for w in _palavras(texto)]
    so_en = sum(w in EN and w not in PT for w in ps)
    so_pt = sum(w in PT and w not in EN for w in ps)
    return (so_en > so_pt) if idioma == "pt" else (so_pt > so_en)


def _voz_3a_pessoa(texto, idioma):
    """Primeira palavra com cara de verbo em 3ª pessoa (PT: -eu/-iu/-ou no passado; EN: lista)."""
    m = re.match(r"\s*([A-Za-zÀ-ÿ]+)", texto)
    if not m:
        return False
    w = m.group(1).lower()
    if idioma == "pt":
        return len(w) >= 5 and w.endswith(("eu", "iu", "ou")) and w != "estou"
    return w in VOZ_3P_EN


def lint_resume(dados, idioma):
    """Avisos (não bloqueiam) sobre idioma e voz dos textos livres do resume.json."""
    avisos = []
    base = dados.get("basics", {})
    resumo = base.get("summary", "")
    if resumo and _destoa(resumo, idioma):
        avisos.append(f"basics.summary parece não estar em {idioma}; revise")
    for i, emprego in enumerate(dados.get("work", [])):
        rotulo = f"work[{i}] ({emprego.get('name', '?')})"
        for j, destaque in enumerate(emprego.get("highlights", []), 1):
            if _destoa(destaque, idioma):
                avisos.append(f"{rotulo} destaque {j} parece não estar em {idioma}: {destaque[:60]}")
            if _voz_3a_pessoa(destaque, idioma):
                avisos.append(f"{rotulo} destaque {j} começa com verbo em 3ª pessoa "
                              f"(use 1ª pessoa): {destaque[:60]}")
    return avisos


def lint(pasta, idioma):
    j = Path(pasta) / "resume.json"
    if not j.is_file():
        return ["resume.json não encontrado na pasta"]
    return lint_resume(json.loads(j.read_text(encoding="utf-8")), idioma)


def pasta_saida(base, data, empresa, cargo):
    p = Path(base) / f"{data}-{_slug(empresa)}-{_slug(cargo)}"
    p.mkdir(parents=True, exist_ok=True)
    return p


def validar_coverage(texto):
    if _secao(texto, "Lacunas") is None:
        return ["falta a seção '## Lacunas' (use 'Nenhuma lacuna identificada.' se não houver)"]
    return []


def _run(cmd, cwd):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()[-500:]


def gerar_pdf(pasta, vendor=VENDOR):
    pasta = Path(pasta)
    scripts = Path(vendor) / UP_SCRIPTS
    j = pasta / "resume.json"
    if not j.is_file():
        return ["resume.json não encontrado na pasta"]
    if not (scripts / "validar_json.py").is_file():
        return ["scripts do upstream ausentes (rode make setup)"]
    if not shutil.which("pdflatex"):
        return ["pdflatex ausente (rode make doctor)"]
    rc, out = _run([sys.executable, str(scripts / "validar_json.py"), str(j)], pasta)
    if rc:
        return ["validar_json.py falhou: " + out]
    tex = pasta / "curriculo.tex"
    rc, out = _run([sys.executable, str(scripts / "json_para_latex.py"), str(j), str(tex)], pasta)
    if rc or not tex.is_file():
        return ["json_para_latex.py falhou: " + out]
    rc, out = _run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error",
                    "-output-directory", str(pasta), str(tex)], pasta)
    if rc or not (pasta / "curriculo.pdf").is_file():
        return ["pdflatex falhou: " + out]
    return []


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("idioma"); i.add_argument("texto"); i.add_argument("--forcar")
    p = sub.add_parser("pasta"); p.add_argument("--empresa", required=True); p.add_argument("--cargo", required=True)
    p.add_argument("--base", default=str(BASE)); p.add_argument("--data", default=date.today().isoformat())
    v = sub.add_parser("coverage"); v.add_argument("arquivo")
    g = sub.add_parser("pdf"); g.add_argument("pasta")
    l = sub.add_parser("lint"); l.add_argument("pasta"); l.add_argument("--idioma", required=True, choices=("en", "pt"))
    a = ap.parse_args(argv)
    if a.cmd == "lint":
        # Só avisa: exit 0 sempre. Falhas de leitura também viram aviso na saída.
        try:
            avisos = lint(a.pasta, a.idioma)
        except (OSError, json.JSONDecodeError) as e:
            avisos = [f"lint não rodou: {e}"]
        print("\n".join(f"AVISO: {x}" for x in avisos) if avisos else "lint de idioma/voz: sem avisos")
        return 0
    if a.cmd == "idioma":
        try:
            print(detectar_idioma(a.texto, a.forcar))
        except ValueError as e:
            print(e, file=sys.stderr); return 2
    elif a.cmd == "pasta":
        print(pasta_saida(a.base, a.data, a.empresa, a.cargo))
    else:
        erros = (validar_coverage(Path(a.arquivo).read_text(encoding="utf-8")) if a.cmd == "coverage"
                 else gerar_pdf(a.pasta))
        for e in erros:
            print("ERRO:", e, file=sys.stderr)
        return 1 if erros else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
