#!/usr/bin/env python3
"""Apoio ao comando /triagem: gate, classificação da entrada, validação e gravação.

  triagem.py check [--busca ..] [--excluidas ..] [--perfil ..]
  triagem.py entrada <texto>            -> imprime link|texto|vazio
  triagem.py salvar <arquivo> --empresa E --cargo C [--vagas private/vagas] [--data AAAA-MM-DD]
"""
import argparse, re, sys, unicodedata
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import validar_config  # noqa: E402

PERFIL = ROOT / "private/perfil/profile_truth.md"
VAGAS = ROOT / "private/vagas"
URL_RE = re.compile(r"^https?://\S+$")
NOTA_RE = re.compile(r"Nota de aderência:\s*(\d+(?:[.,]\d+)?)\s*/\s*10", re.I)


def preflight(busca, excluidas, perfil):
    probs = validar_config.validate(busca, excluidas)
    if not Path(perfil).is_file():
        probs.append(validar_config.Problem(Path(perfil), 0, "profile_truth.md não encontrado (rode make setup)"))
    return probs


def classificar_entrada(arg):
    s = arg.strip()
    if not s:
        return "vazio"
    return "link" if URL_RE.match(s) else "texto"


def _slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def caminho_triagem(vagas, data, empresa, cargo):
    return Path(vagas) / f"{data}-triagem-{_slug(empresa)}-{_slug(cargo)}.md"


def _secao(texto, nome):
    m = re.search(rf"^##\s+{nome}\s*$(.*?)(?=^##\s|\Z)", texto, re.M | re.S | re.I)
    return m.group(1).strip() if m else None


def validar_saida(texto):
    erros = []
    m = NOTA_RE.search(texto)
    if not m:
        erros.append('falta "Nota de aderência: N/10"')
    elif not 0 <= float(m.group(1).replace(",", ".")) <= 10:
        erros.append("nota de aderência fora de 0 a 10")
    for nome in ("Motivos", "Lacunas"):
        c = _secao(texto, nome)
        if c is None:
            erros.append(f"falta a seção '## {nome}'")
        elif not c:
            erros.append(f"seção '## {nome}' vazia (se não há lacunas, diga explicitamente)")
    return erros


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check")
    c.add_argument("--busca", default=str(ROOT / "busca.yaml"))
    c.add_argument("--excluidas", default=str(ROOT / "private/perfil/vagas_excluidas.md"))
    c.add_argument("--perfil", default=str(PERFIL))
    e = sub.add_parser("entrada")
    e.add_argument("texto")
    s = sub.add_parser("salvar")
    s.add_argument("arquivo")
    s.add_argument("--empresa", required=True)
    s.add_argument("--cargo", required=True)
    s.add_argument("--vagas", default=str(VAGAS))
    s.add_argument("--data", default=date.today().isoformat())
    a = ap.parse_args(argv)

    if a.cmd == "check":
        probs = preflight(a.busca, a.excluidas, a.perfil)
        for p in probs:
            print(p, file=sys.stderr)
        if probs:
            print(f"Configuração incompleta ({len(probs)} problema(s)). /triagem não vai rodar.", file=sys.stderr)
            return 1
        print("Configuração OK.")
        return 0
    if a.cmd == "entrada":
        print(classificar_entrada(a.texto))
        return 0
    texto = Path(a.arquivo).read_text(encoding="utf-8")
    erros = validar_saida(texto)
    if erros:
        for x in erros:
            print(f"{a.arquivo}: {x}", file=sys.stderr)
        return 1
    dest = caminho_triagem(a.vagas, a.data, a.empresa, a.cargo)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(texto, encoding="utf-8")
    print(dest)
    return 0


if __name__ == "__main__":
    sys.exit(main())
