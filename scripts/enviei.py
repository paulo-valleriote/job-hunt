#!/usr/bin/env python3
"""Registra no tracker uma candidatura JÁ enviada pelo usuário.
Só escreve em private/tracker.csv; nunca envia nada a ninguém."""
import argparse, csv, datetime, re, sys, unicodedata
from pathlib import Path

HEADER = ["data", "empresa", "vaga", "fonte", "tipo", "link", "curriculo",
          "status", "proximo_passo", "observacoes"]


def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def find_resume(private, empresa, vaga):
    base = private / "curriculos"
    if not base.is_dir():
        return ""
    se, sv = slug(empresa), slug(vaga)
    hits = sorted(d.name for d in base.iterdir()
                  if d.is_dir() and d.name.endswith(f"-{se}-{sv}"))
    return f"curriculos/{hits[-1]}" if hits else ""


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--private", default="private")
    ap.add_argument("--empresa", required=True)
    ap.add_argument("--vaga", required=True)
    ap.add_argument("--fonte", default="")
    ap.add_argument("--tipo", default="")
    ap.add_argument("--link", default="")
    ap.add_argument("--status", default="enviada")
    ap.add_argument("--proximo-passo", default="")
    ap.add_argument("--observacoes", default="")
    ap.add_argument("--data", default=datetime.date.today().isoformat())
    a = ap.parse_args(argv)

    private = Path(a.private)
    path = private / "tracker.csv"
    if not path.is_file():
        print(f"ERRO: {path} não existe. Rode `make setup` primeiro.", file=sys.stderr)
        return 1
    with open(path, newline="", encoding="utf-8-sig") as f:
        existing = list(csv.reader(f))
    header = existing[0] if existing else HEADER
    body = [r for r in existing[1:] if r]
    key = (slug(a.empresa), slug(a.vaga))
    ie, iv = header.index("empresa"), header.index("vaga")
    if any((slug(r[ie]), slug(r[iv])) == key for r in body if len(r) > max(ie, iv)):
        print(f"já registrada: {a.empresa} / {a.vaga} (nada alterado)")
        return 0

    vals = {"data": a.data, "empresa": a.empresa, "vaga": a.vaga, "fonte": a.fonte,
            "tipo": a.tipo, "link": a.link, "curriculo": find_resume(private, a.empresa, a.vaga),
            "status": a.status, "proximo_passo": a.proximo_passo, "observacoes": a.observacoes}
    body.append([vals.get(c, "") for c in header])
    # utf-8 com BOM e CRLF: abre direto no Excel
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, lineterminator="\r\n")
        w.writerow(header)
        w.writerows(body)
    print(f"registrada: {a.empresa} / {a.vaga}" + (f" (currículo: {vals['curriculo']})" if vals["curriculo"] else " (sem currículo gerado)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
