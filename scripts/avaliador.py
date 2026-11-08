#!/usr/bin/env python3
"""Ciclo avaliador/revisão do /curriculo (Guardrail 8).

Layout na pasta do currículo: versoes/vN/{resume.json,avaliacao.json}.

  avaliador.py validar <avaliacao.json>   -> valida o JSON do avaliador
  avaliador.py decidir <pasta> [--max-revisoes N] -> imprime 'revisar' ou 'parar: <motivo>'
  avaliador.py finalizar <pasta>          -> copia a de melhor nota p/ resume.json e grava rating_report.md

O teto de revisões (padrão 3) vem de --max-revisoes ou da variável JOBHUNT_MAX_REVISOES.
"""
import argparse, json, os, re, shutil, sys
from pathlib import Path

ALVO = 8.5
MAX_REV = 3
CAMPOS = ("nota", "pontos_fortes", "lacunas", "palavras_chave")


def validar_avaliacao(d):
    erros = [f"campo ausente: {c}" for c in CAMPOS if c not in d]
    n = d.get("nota")
    if "nota" in d and (isinstance(n, bool) or not isinstance(n, (int, float)) or not 1 <= n <= 10):
        erros.append("nota deve ser número de 1 a 10")
    for c in CAMPOS[1:]:
        if c in d and not isinstance(d[c], list):
            erros.append(f"{c} deve ser lista")
    return erros


def decidir(notas, alvo=ALVO, max_rev=MAX_REV):
    """notas: nota de cada versão em ordem. Retorna ('revisar'|'parar', motivo)."""
    if notas[-1] >= alvo:
        return "parar", f"nota-alvo {alvo} atingida"
    if len(notas) > 1 and notas[-1] <= max(notas[:-1]):
        return "parar", "a última revisão não melhorou a nota"
    if len(notas) - 1 >= max_rev:
        return "parar", f"máximo de {max_rev} revisões atingido"
    return "revisar", ""


def _teto(arg=None):
    return arg if arg is not None else int(os.environ.get("JOBHUNT_MAX_REVISOES", MAX_REV))


def _versoes(pasta):
    dirs = sorted((p for p in (Path(pasta) / "versoes").glob("v*") if re.fullmatch(r"v\d+", p.name)),
                  key=lambda p: int(p.name[1:]))
    return [(int(p.name[1:]), p, json.loads((p / "avaliacao.json").read_text(encoding="utf-8")))
            for p in dirs if (p / "avaliacao.json").is_file()]


def _notas(pasta):
    vs = _versoes(pasta)
    if not vs:
        raise ValueError("nenhuma versão avaliada em versoes/")
    return vs, [v[2]["nota"] for v in vs]


def finalizar(pasta, max_rev=None):
    vs, notas = _notas(pasta)
    melhor = max(range(len(notas)), key=lambda i: (notas[i], -i))  # empate: a mais antiga
    n, dirv, av = vs[melhor]
    shutil.copyfile(dirv / "resume.json", Path(pasta) / "resume.json")
    acao, motivo = decidir(notas, max_rev=_teto(max_rev))
    if acao == "revisar":
        motivo = "ciclo interrompido antes de uma condição de parada"
    linhas = ["# Rating report", "", "## Histórico de notas", "", "| Versão | Nota |", "|---|---|"]
    linhas += [f"| v{k} | {a['nota']} |" for k, _, a in vs]
    linhas += ["", f"Motivo da parada: {motivo}", f"Entregue: v{n} (nota {av['nota']})", "",
               f"## Avaliação da versão entregue (v{n})", "", "Pontos fortes:"]
    linhas += [f"- {x}" for x in av["pontos_fortes"]] + ["", "Lacunas:"]
    linhas += [f"- {x}" for x in av["lacunas"]] + ["", "Palavras-chave: " + ", ".join(av["palavras_chave"]), ""]
    (Path(pasta) / "rating_report.md").write_text("\n".join(linhas), encoding="utf-8")
    return n


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("validar").add_argument("arquivo")
    for nome in ("decidir", "finalizar"):
        s = sub.add_parser(nome); s.add_argument("pasta"); s.add_argument("--max-revisoes", type=int)
    a = ap.parse_args(argv)
    try:
        if a.cmd == "validar":
            erros = validar_avaliacao(json.loads(Path(a.arquivo).read_text(encoding="utf-8")))
            for e in erros:
                print("ERRO:", e, file=sys.stderr)
            return 1 if erros else 0
        if a.cmd == "decidir":
            _, notas = _notas(a.pasta)
            acao, motivo = decidir(notas, max_rev=_teto(a.max_revisoes))
            print(f"{acao}: {motivo}" if motivo else acao)
        else:
            print(f"entregue: v{finalizar(a.pasta, a.max_revisoes)}")
    except (ValueError, OSError, json.JSONDecodeError, KeyError) as e:
        print("ERRO:", e, file=sys.stderr); return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
