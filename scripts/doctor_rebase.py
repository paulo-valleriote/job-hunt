#!/usr/bin/env python3
"""Diagnóstico do Catálogo Rebase para `make doctor`: confere private/rebase.env e TOKEN e faz uma
única chamada GET /api/v1/jobs?por_pagina=1. Sem TOKEN não chama a API. O token nunca é impresso.

Uso: python3 scripts/doctor_rebase.py [--base URL] [--env ARQUIVO]   (saída 0 se ok; 1 se não)
"""
import argparse, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rebase as rb  # noqa: E402


def main(argv=None, fetch=rb.http_get):
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=rb.BASE)
    ap.add_argument("--env", default=str(rb.ENV_ARQUIVO))
    a = ap.parse_args(argv)
    token = rb.ler_token(Path(a.env))
    if not token:
        print(f"FALTA - Rebase: TOKEN ausente: {rb.mensagem_token_ausente()}")
        return 1
    ok, texto = rb.checar_token(token, base=a.base, fetch=fetch)
    print(f"{'ok    ' if ok else 'FALTA '}- Rebase: {texto}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
