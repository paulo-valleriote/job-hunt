#!/usr/bin/env python3
"""Apoio do /busca: gate, janela de data, URLs de busca do LinkedIn, validação e arquivo final.

A coleta em si é feita pelo Claude no navegador (Claude in Chrome, com login do usuário); este
script só faz a parte determinística. Subcomandos (todos passam antes por validar_config):
  urls     imprime a data "desde" e as URLs de busca (só cargo, local, regime e janela de data)
  gravar   lê JSON de candidatos, descarta inválidas/excluídas/duplicadas e grava AAAA-MM-DD-busca.md
"""
import argparse, json, re, sys
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlencode, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
import validar_config  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
JANELA_PADRAO, JANELA_MAX = 7, 30
# LinkedIn entende melhor o nome do local em inglês.
LOCAIS = {"brasil": "Brazil", "eua": "United States", "estados unidos": "United States",
          "reino unido": "United Kingdom", "portugal": "Portugal", "canadá": "Canada",
          "canada": "Canada", "alemanha": "Germany", "europa": "European Union",
          "latam": "Latin America", "américa latina": "Latin America", "mundo": "Worldwide"}
REGIMES = {"presencial": "1", "remoto": "2", "híbrido": "3", "hibrido": "3"}
GRUPOS = (("simplificada", "Candidatura simplificada (dentro do LinkedIn)"),
          ("externa", "Candidatura externa (site da empresa / ATS)"))


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


def janela_desde(saida_dir, hoje):
    """Publicadas desde a última busca (mesmo dia inclusive); sem busca anterior, 7 dias; teto 30."""
    datas = []
    for p in Path(saida_dir).glob("*-busca.md"):
        try:
            datas.append(date.fromisoformat(p.name[:10]))
        except ValueError:
            pass
    anteriores = [d for d in datas if d < hoje]
    desde = max(anteriores) if anteriores else hoje - timedelta(days=JANELA_PADRAO)
    return max(desde, hoje - timedelta(days=JANELA_MAX))


def build_urls(cfg, desde, hoje):
    """Uma URL por cargo x local. NUNCA inclui nada além de cargo, local, regime e janela."""
    segundos = max(1, (hoje - desde).days + 1) * 86400
    wt = REGIMES.get(_norm(cfg.get("regime", "")))
    urls = []
    for cargo in cfg.get("cargos_alvo", []):
        for pais in cfg.get("paises_fuso") or [""]:
            q = {"keywords": cargo}
            if pais:
                q["location"] = LOCAIS.get(_norm(pais), pais)
            q["f_TPR"] = f"r{segundos}"
            if wt:
                q["f_WT"] = wt
            q["sortBy"] = "DD"
            urls.append("https://www.linkedin.com/jobs/search/?" + urlencode(q))
    return urls


def _norm(s):
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def _link_key(link):
    m = re.search(r"/jobs/view/(?:[^/?#]*-)?(\d{6,})", link or "")
    if m:
        return f"linkedin:{m.group(1)}"
    u = urlsplit((link or "").strip().lower())
    return f"{u.netloc}{u.path.rstrip('/')}"


def _excluidas_terms(text):
    return [_norm(l) for l in text.splitlines() if l.strip() and not l.lstrip().startswith("#")]


def _data(v):
    try:
        return date.fromisoformat((v.get("data") or "").strip()[:10])
    except ValueError:
        return None


def processar(vagas, excluidas_text, desde=None, hoje=None):
    """Devolve (aceitas, descartadas). Descartada = {titulo, empresa, link, motivo}."""
    linhas = _excluidas_terms(excluidas_text)
    vistos_link, vistos_te, out, fora = set(), set(), [], []

    def descarta(v, motivo):
        fora.append({"titulo": v.get("titulo", ""), "empresa": v.get("empresa", ""),
                     "link": v.get("link", ""), "motivo": motivo})

    for v in vagas:
        emp = _norm(v.get("empresa"))
        lk = _link_key(v.get("link"))
        d = _data(v)
        if (emp and any(emp in l for l in linhas)) or (lk and any(lk in l for l in linhas)):
            descarta(v, "consta em vagas_excluidas.md")
            continue
        status = _norm(v.get("status") or "aberta")
        if status != "aberta":
            descarta(v, f"não aceita mais candidaturas ({status})")
            continue
        if d is None:
            descarta(v, "sem data de publicação verificada")
            continue
        if desde and d < desde:
            descarta(v, f"publicada em {d}, antes de {desde}")
            continue
        if hoje and d > hoje:
            descarta(v, f"data inválida ({d})")
            continue
        te = (_norm(v.get("titulo")), emp)
        if (lk and lk in vistos_link) or te in vistos_te:
            descarta(v, "duplicada")
            continue
        if lk:
            vistos_link.add(lk)
        vistos_te.add(te)
        out.append(v)
    return out, fora


def _grupo(v):
    return "externa" if _norm(v.get("candidatura")) == "externa" else "simplificada"


def render(vagas, data, descartadas=(), desde=None):
    cab = f"{len(vagas)} vaga(s), sem classificação"
    if desde:
        cab += f", publicadas desde {desde}"
    L = [f"# Busca de vagas {data}", "", cab + ". Escolha quais triar com /triagem.", ""]
    n = 0
    for chave, titulo in GRUPOS:
        grupo = [v for v in vagas if _grupo(v) == chave]
        if not grupo:
            continue
        L += [f"# {titulo}", ""]
        for v in grupo:
            n += 1
            L += [f"## {n}. {v.get('titulo', '')}", f"- Empresa: {v.get('empresa', '')}",
                  f"- Local: {v.get('local', '')}", f"- Data: {v.get('data', '')}",
                  f"- Candidatura: {chave}", f"- Link: {v.get('link', '')}",
                  f"- Trecho: {v.get('requisitos') or v.get('trecho', '')}", ""]
    if descartadas:
        L += ["# Descartadas", ""]
        L += [f"- {d['titulo']} | {d['empresa']} | {d['motivo']} | {d['link']}" for d in descartadas]
        L.append("")
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["urls", "gravar"])
    ap.add_argument("--busca", default=str(ROOT / "busca.yaml"))
    ap.add_argument("--excluidas", default=str(ROOT / "private/perfil/vagas_excluidas.md"))
    ap.add_argument("--resultados")
    ap.add_argument("--saida-dir", default=str(ROOT / "private/vagas"))
    ap.add_argument("--data", default=date.today().isoformat())
    ap.add_argument("--desde", help="AAAA-MM-DD; padrão: data da última busca")
    a = ap.parse_args(argv)
    probs = validar_config.validate(a.busca, a.excluidas)
    if probs:
        for p in probs:
            print(p, file=sys.stderr)
        print(f"Configuração incompleta ({len(probs)} problema(s)) ou de exemplo. /busca recusa rodar.",
              file=sys.stderr)
        return 1
    hoje = date.fromisoformat(a.data)
    desde = date.fromisoformat(a.desde) if a.desde else janela_desde(a.saida_dir, hoje)
    if a.cmd == "urls":
        cfg = parse_busca(Path(a.busca).read_text(encoding="utf-8"))
        print(f"desde {desde}")
        print("\n".join(build_urls(cfg, desde, hoje)))
        return 0
    if not a.resultados:
        print("--resultados é obrigatório em 'gravar'", file=sys.stderr)
        return 2
    vagas = json.loads(Path(a.resultados).read_text(encoding="utf-8"))
    final, fora = processar(vagas, Path(a.excluidas).read_text(encoding="utf-8"), desde, hoje)
    out = Path(a.saida_dir)
    out.mkdir(parents=True, exist_ok=True)
    dest = out / f"{a.data}-busca.md"
    dest.write_text(render(final, a.data, fora, desde), encoding="utf-8")
    print(f"{len(final)} vaga(s) gravada(s) em {dest}; {len(fora)} descartada(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
