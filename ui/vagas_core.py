"""Lógica da tela Vagas, sem Streamlit. A UI só lê private/vagas e chama `claude -p "/triagem ..."`;
gate, validação e gravação continuam em scripts/triagem.py (via o comando /triagem)."""
import re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import triagem as _triagem  # noqa: E402

VAGAS = ROOT / "private/vagas"


class TriagemFalhou(RuntimeError):
    pass


def ultima_busca(vagas_dir=VAGAS):
    arqs = sorted(Path(vagas_dir).glob("*-busca.md"))
    if not arqs:
        return None
    arq = arqs[-1]
    texto = arq.read_text(encoding="utf-8")
    vagas = []
    for bloco in re.split(r"^##\s+\d+\.\s*", texto, flags=re.M)[1:]:
        titulo, _, resto = bloco.partition("\n")
        v = {"titulo": titulo.strip()}
        for chave in ("empresa", "link", "data", "trecho"):
            m = re.search(rf"^- {chave}:[ \t]*(.*)$", resto, re.M | re.I)
            v[chave] = m.group(1).strip() if m else ""
        vagas.append(v)
    return {"arquivo": arq, "data": arq.name[:10], "vagas": vagas}


def ler_triagem(texto):
    m = _triagem.NOTA_RE.search(texto)
    return {"nota": float(m.group(1).replace(",", ".")) if m else None,
            "motivos": _triagem._secao(texto, "Motivos") or "",
            "lacunas": _triagem._secao(texto, "Lacunas") or "",
            "texto": texto}


def _estado(vagas_dir):
    return {p.name: p.stat().st_mtime_ns for p in Path(vagas_dir).glob("*-triagem-*.md")}


def _claude(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    return p.returncode, (p.stdout + p.stderr).strip()


def triar(entrada, vagas_dir=VAGAS, runner=_claude):
    entrada = entrada.strip()
    if not entrada:
        raise ValueError("Cole um link ou o texto da vaga.")
    antes = _estado(vagas_dir)
    code, saida = runner(["claude", "-p", f"/triagem {entrada}"])
    novos = [n for n, m in _estado(vagas_dir).items() if antes.get(n) != m]
    if code != 0 or not novos:
        raise TriagemFalhou(saida or "A triagem não gerou arquivo.")
    r = ler_triagem((Path(vagas_dir) / sorted(novos)[-1]).read_text(encoding="utf-8"))
    r["arquivo"] = sorted(novos)[-1]
    r["saida"] = saida
    return r
