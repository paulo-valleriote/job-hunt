"""Lógica das telas Currículos e Tracker, sem Streamlit. A UI só lê private/ e chama
`claude -p "/curriculo ..."`; geração, avaliação e anti-invenção ficam nos scripts/comandos.
O tracker usa o mesmo formato de scripts/enviei.py (utf-8 com BOM, CRLF, abre no Excel)."""
import csv, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import enviei as _enviei  # noqa: E402

BASE = ROOT / "private/curriculos"
PRIVATE = ROOT / "private"
NOTA_RE = re.compile(r"Entregue:\s*v\d+\s*\(nota\s*([\d.,]+)\)")


class GeracaoFalhou(RuntimeError):
    pass


def _ler(p):
    return p.read_text(encoding="utf-8") if p.is_file() else None


def listar(base=BASE):
    base = Path(base)
    if not base.is_dir():
        return []
    itens = []
    for d in sorted((x for x in base.iterdir() if x.is_dir()), key=lambda x: x.name, reverse=True):
        rating = _ler(d / "rating_report.md")
        m = NOTA_RE.search(rating) if rating else None
        itens.append({"nome": d.name, "pasta": d,
                      "pdf": d / "curriculo.pdf" if (d / "curriculo.pdf").is_file() else None,
                      "nota": float(m.group(1).replace(",", ".")) if m else None,
                      "rating": rating, "coverage": _ler(d / "coverage_review.md"),
                      "anti_invencao": _ler(d / "anti_invencao.md")})
    return itens


def _claude(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    return p.returncode, (p.stdout + p.stderr).strip()


def gerar(entrada, base=BASE, runner=_claude):
    entrada = entrada.strip()
    if not entrada:
        raise ValueError("Cole um link ou o texto da vaga.")
    antes = {x["nome"]: (x["pasta"].stat().st_mtime_ns) for x in listar(base)}
    code, saida = runner(["claude", "-p", f"/curriculo {entrada}"])
    novos = [x for x in listar(base) if antes.get(x["nome"]) != x["pasta"].stat().st_mtime_ns]
    if code != 0 or not novos:
        raise GeracaoFalhou(saida or "O comando não gerou currículo.")
    novos[0]["saida"] = saida
    return novos[0]


def ler_tracker(private=PRIVATE):
    path = Path(private) / "tracker.csv"
    if not path.is_file():
        return None
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = [r for r in csv.reader(f) if r]
    cab = rows[0] if rows else list(_enviei.HEADER)
    return cab, [dict(zip(cab, r + [""] * (len(cab) - len(r)))) for r in rows[1:]]


def salvar_tracker(private, cab, linhas):
    with open(Path(private) / "tracker.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, lineterminator="\r\n")
        w.writerow(cab)
        w.writerows([[str(l.get(c) or "") for c in cab] for l in linhas])
