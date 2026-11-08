#!/usr/bin/env python3
"""Apoio ao comando /curriculo (básico): idioma, pasta de saída, coverage e PDF.

  curriculo.py idioma <texto da vaga> [--forcar en|pt]   -> imprime en|pt
  curriculo.py pasta --empresa E --cargo C [--base private/curriculos] [--data AAAA-MM-DD] -> imprime o caminho
  curriculo.py coverage <coverage_review.md>             -> valida o relatório
  curriculo.py pdf <pasta>                               -> resume.json -> .tex -> PDF

Heurística de idioma: conta stopwords EN vs PT no texto da vaga; empate cai em EN
(foco do usuário). O modelo só decide se o texto for ambíguo/misto (ver /curriculo).
"""
import argparse, re, shutil, subprocess, sys
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
    a = ap.parse_args(argv)
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
