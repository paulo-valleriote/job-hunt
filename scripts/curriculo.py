#!/usr/bin/env python3
"""Apoio ao comando /curriculo (básico): idioma, pasta de saída, coverage e PDF.

  curriculo.py idioma <texto da vaga> [--forcar en|pt]   -> imprime en|pt
  curriculo.py pasta --empresa E --cargo C [--base private/curriculos] [--data AAAA-MM-DD] -> imprime o caminho
  curriculo.py lint <pasta> --idioma en|pt               -> avisos de idioma e voz (exit 0 sempre)
  curriculo.py coverage <coverage_review.md>             -> valida o relatório
  curriculo.py pdf <pasta> [--idioma en|pt]              -> resume.json -> .tex -> PDF

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


# Palavras do espanhol que não existem em português, para o espanhol não ser confundido com pt.
ES = set("el los las y del en un es nosotros nuestro nuestra equipo experiencia usted trabajo desarrollo "
         "requisitos años también más pero tu tus sobre".split())


def detectar_idioma(texto, forcar=None):
    """Só existem currículos em pt e en: vaga em outro idioma (espanhol, francês...) cai em en."""
    if forcar:
        if forcar not in ("en", "pt"):
            raise ValueError("idioma deve ser en ou pt")
        return forcar
    palavras = re.findall(r"[a-záàâãéêíóôõúçñ]+", texto.lower())
    en = sum(w in EN for w in palavras)
    pt = sum(w in PT for w in palavras)
    es = sum(w in ES for w in palavras)
    return "pt" if pt > en and pt > es else "en"


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


ROTULOS_EN = {"Resumo": "Summary", "Experiência": "Experience", "Projetos": "Projects",
              "Competências": "Skills", "Formação": "Education", "Certificações": "Certifications",
              "Idiomas": "Languages"}


def _traduzir_rotulos(tex):
    """O template do upstream imprime rótulos em português; num currículo em inglês, troca por inglês."""
    for pt, en in ROTULOS_EN.items():
        tex = tex.replace(f"\\section*{{{pt}}}", f"\\section*{{{en}}}")
    return tex.replace(" -- Atual", " -- Present")


def _span_secao(tex, nomes):
    """(início, fim) do conteúdo da seção cujo título está em `nomes`; None se não existe."""
    ini = re.search(r"\\section\*\{(%s)\}" % "|".join(nomes), tex)
    if not ini:
        return None
    prox = re.search(r"\\section\*\{", tex[ini.end():])
    return ini.end(), (ini.end() + prox.start() if prox else len(tex))


CERT_ITEM = re.compile(r"^  \\item (?P<nome>.*?)(?: \((?P<st>valid|expired[^()]*|in progress)\))?"
                       r"(?: \((?P<emi>.*)\))?$")


def _situacao(st, idioma):
    if idioma != "pt":
        return st
    if st.startswith("expired"):
        resto = st[len("expired"):].strip()
        return f"expirada em {resto}" if resto else "expirada"
    return {"valid": "válida", "in progress": "em andamento"}.get(st, st)


def _ajustar_certificacoes(tex, idioma):
    """'Nome (expired 08/2026) (Emissor)' vira 'Nome, Emissor \\hfill expired 08/2026': a situação (que vai no
    nome por não haver campo no esquema) sai dos parênteses e fica alinhada à direita, como as datas."""
    span = _span_secao(tex, ("Certificações", "Certifications"))
    if not span:
        return tex
    linhas = []
    for l in tex[span[0]:span[1]].split("\n"):
        m = CERT_ITEM.match(l)
        if m and l.startswith("  \\item "):
            l = "  \\item " + m["nome"] + (f", {m['emi']}" if m["emi"] else "")
            if m["st"]:
                l += f" \\hfill {_situacao(m['st'], idioma)}"
        linhas.append(l)
    return tex[:span[0]] + "\n".join(linhas) + tex[span[1]:]


def _ajustar_formacao(tex, idioma):
    """Linhas da Formação saem como '<tipo> em <área>': sem área sobra um 'em' solto; sem tipo, sobra um 'em' no começo."""
    ini = re.search(r"\\section\*\{(Formação|Education)\}", tex)
    if not ini:
        return tex
    fim = re.search(r"\\section\*\{", tex[ini.end():])
    fim = ini.end() + fim.start() if fim else len(tex)
    bloco = tex[ini.end():fim]
    bloco = re.sub(r"\\textbf\{ em ", r"\\textbf{", bloco)          # sem tipo
    bloco = re.sub(r"(\\textbf\{[^}]*?) em \}", r"\1}", bloco)       # sem área
    if idioma == "en":
        bloco = re.sub(r"(\\textbf\{[^}]*?) em ", r"\1 in ", bloco)
    return tex[:ini.end()] + bloco + tex[fim:]


def ajustar_latex(tex, idioma="pt"):
    """Ajustes sobre o .tex gerado pelo upstream (vendor/ não é versionado, então o ajuste é feito aqui):
    espaçamento (itens mais juntos, experiências mais separadas), rótulos por idioma e Formação sem 'em' solto."""
    if idioma == "en":
        tex = _traduzir_rotulos(tex)
    tex = _ajustar_formacao(tex, idioma)
    tex = _ajustar_certificacoes(tex, idioma)
    tex = tex.replace("itemsep=1pt,topsep=2pt}", "itemsep=0pt,parsep=0pt,topsep=1pt}")
    # cabeçalho da experiência terminado em \\ antes da lista deixa uma linha vazia: troca por \par
    cab = re.compile(r"^(\\textbf\{.*\\hfill .*)\\\\\n(?=\\begin\{itemize\})", re.M)
    n = 0

    def _cab(m):
        nonlocal n
        n += 1
        antes = "" if n == 1 else "\\vspace{9pt}\n"
        return f"{antes}{m.group(1)}\\par\\nobreak\n"

    return cab.sub(_cab, tex)


def _idioma_do_resume(j):
    """Idioma do currículo, inferido dos textos livres do resume.json (usado quando --idioma não é passado)."""
    try:
        d = json.loads(Path(j).read_text(encoding="utf-8"))
        textos = [d.get("basics", {}).get("summary", "")]
        textos += [h for w in d.get("work", []) for h in w.get("highlights", [])]
        return detectar_idioma(" ".join(textos))
    except (OSError, ValueError, AttributeError, TypeError):
        return "pt"


def gerar_pdf(pasta, vendor=VENDOR, idioma=None):
    pasta = Path(pasta).resolve()  # os subprocessos rodam com cwd=pasta: caminho relativo quebraria
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
    idioma = idioma or _idioma_do_resume(j)
    tex.write_text(ajustar_latex(tex.read_text(encoding="utf-8"), idioma), encoding="utf-8")
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
    g = sub.add_parser("pdf"); g.add_argument("pasta"); g.add_argument("--idioma", choices=("en", "pt"))
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
                 else gerar_pdf(a.pasta, idioma=a.idioma))
        for e in erros:
            print("ERRO:", e, file=sys.stderr)
        return 1 if erros else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
