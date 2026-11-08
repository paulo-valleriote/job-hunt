#!/usr/bin/env python3
"""Apoio do /busca: gate, consultas externas, deduplicação, filtro de excluídas e arquivo final.

A busca em si (WebSearch) é feita pelo Claude no comando /busca; este script só faz a parte
determinística. Subcomandos (ambos passam antes por validar_config e recusam se houver problema):
  queries  imprime as consultas de WebSearch (só cargo, local e regime)
  gravar   lê JSON de candidatos, deduplica, remove excluídas e grava AAAA-MM-DD-busca.md
"""
import argparse, json, re, sys
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
import validar_config  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def parse_busca(text):
    """Subconjunto de YAML aceito pelo gate: 'chave: valor' ou 'chave:' + itens '- valor'."""
    out, cur = {}, None
    for raw in text.splitlines():
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        m = re.match(r"^([A-Za-z_]+):(.*)$", raw)
        if m and not raw.startswith(" "):
            cur = m.group(1)
            val = validar_config._strip(m.group(2))
            out[cur] = val if val else []
        elif s.startswith("- ") and cur is not None:
            if not isinstance(out[cur], list):
                out[cur] = [out[cur]]
            out[cur].append(validar_config._strip(s[2:]))
    return out


def build_queries(cfg):
    """Uma consulta por cargo x país. NUNCA inclui nada além de cargo, local e regime."""
    paises = cfg.get("paises_fuso") or [""]
    return [" ".join(p for p in (cargo, cfg.get("regime", ""), pais, "site:linkedin.com/jobs") if p)
            for cargo in cfg.get("cargos_alvo", []) for pais in paises]


def _norm(s):
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def _link_key(link):
    u = urlsplit((link or "").strip().lower())
    return f"{u.netloc}{u.path.rstrip('/')}"


def _excluidas_terms(text):
    return [_norm(l) for l in text.splitlines() if l.strip() and not l.lstrip().startswith("#")]


def processar(vagas, excluidas_text):
    linhas = _excluidas_terms(excluidas_text)
    vistos_link, vistos_te, out = set(), set(), []
    for v in vagas:
        emp = _norm(v.get("empresa"))
        lk = _link_key(v.get("link"))
        if (emp and any(emp in l for l in linhas)) or (lk and any(lk in l for l in linhas)):
            continue
        te = (_norm(v.get("titulo")), emp)
        if (lk and lk in vistos_link) or te in vistos_te:
            continue
        if lk:
            vistos_link.add(lk)
        vistos_te.add(te)
        out.append(v)
    return out


def render(vagas, data):
    L = [f"# Busca de vagas {data}", "",
         f"{len(vagas)} vaga(s), sem classificação. Escolha quais triar com /triagem.", ""]
    for i, v in enumerate(vagas, 1):
        L += [f"## {i}. {v.get('titulo', '')}", f"- Empresa: {v.get('empresa', '')}",
              f"- Link: {v.get('link', '')}", f"- Data: {v.get('data', '')}",
              f"- Trecho: {v.get('trecho', '')}", ""]
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["queries", "gravar"])
    ap.add_argument("--busca", default=str(ROOT / "busca.yaml"))
    ap.add_argument("--excluidas", default=str(ROOT / "private/perfil/vagas_excluidas.md"))
    ap.add_argument("--resultados")
    ap.add_argument("--saida-dir", default=str(ROOT / "private/vagas"))
    ap.add_argument("--data", default=date.today().isoformat())
    a = ap.parse_args(argv)
    probs = validar_config.validate(a.busca, a.excluidas)
    if probs:
        for p in probs:
            print(p, file=sys.stderr)
        print(f"Configuração incompleta ({len(probs)} problema(s)) ou de exemplo. /busca recusa rodar.",
              file=sys.stderr)
        return 1
    if a.cmd == "queries":
        print("\n".join(build_queries(parse_busca(Path(a.busca).read_text(encoding="utf-8")))))
        return 0
    if not a.resultados:
        print("--resultados é obrigatório em 'gravar'", file=sys.stderr)
        return 2
    vagas = json.loads(Path(a.resultados).read_text(encoding="utf-8"))
    final = processar(vagas, Path(a.excluidas).read_text(encoding="utf-8"))
    out = Path(a.saida_dir)
    out.mkdir(parents=True, exist_ok=True)
    dest = out / f"{a.data}-busca.md"
    dest.write_text(render(final, a.data), encoding="utf-8")
    print(f"{len(final)} vaga(s) gravada(s) em {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
