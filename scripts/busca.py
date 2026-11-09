#!/usr/bin/env python3
"""Apoio do /busca: gate, janela de data, URLs de busca do LinkedIn, validação e arquivo final.

A coleta em si é feita pelo Claude no navegador (Chromium do WSL com porta de debug, via MCP
chrome-devtools, com login do usuário); este script só faz a parte determinística. Subcomandos (todos passam antes por validar_config):
  urls     imprime a data "desde" e as URLs de busca (só cargo, local, regime e janela de data)
  filtros  lista os filtros que o LinkedIn aplicou além do pedido, a partir da URL final
  candidatos  da listagem de todas as URLs, tira os de nível acima (titulos_excluidos) e escolhe
              em rodízio quem será aberto e verificado
  gravar   lê JSON das vagas verificadas, valida o contrato, aplica as regras de processar() e grava
           AAAA-MM-DD-busca.md (as regras de descarte estão documentadas só em processar())
"""
import argparse, json, re, sys, unicodedata
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
import validar_config  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
JANELA_PADRAO, JANELA_MAX = 7, 30
MAX_VAGAS = 20  # o método pede de 10 a 20 vagas por rodada
# Parâmetros da URL final do LinkedIn que pedimos ou que são só navegação; o resto é filtro dele.
PARAMS_ESPERADOS = {"keywords", "location", "geoId", "f_TPR", "f_WT", "sortBy", "currentJobId",
                    "origin", "lipi", "skipRedirect", "infoNotice", "referralSearchId"}
POR_URL, TOTAL_CANDIDATOS = 5, 25  # candidatos abertos por URL e no total, antes da verificação
# LinkedIn entende melhor o nome do local em inglês.
LOCAIS = {"brasil": "Brazil", "eua": "United States", "estados unidos": "United States",
          "reino unido": "United Kingdom", "portugal": "Portugal", "canadá": "Canada",
          "canada": "Canada", "alemanha": "Germany", "europa": "European Union",
          "latam": "Latin America", "américa latina": "Latin America", "mundo": "Worldwide"}
# O LinkedIn descarta "location=" e usa a localidade da conta; o geoId fixa o país. Só entram
# os códigos verificados no navegador (outros países seguem só com location).
# Receita para achar e confirmar um código novo: docs/agents/busca-geoid.md
GEO_IDS = {"Brazil": "106057199", "United States": "103644278", "United Kingdom": "101165590",
           "Latin America": "91000011"}
ELEGIVEL = ("brasil", "latam", "mundo")  # onde a vaga remota aceita candidatos
# Contrato do JSON que o /busca entrega ao `gravar` (valor vazio = "página não mostrou").
VALORES = {"modalidade": ("", "remoto", "hibrido", "híbrido", "presencial"),
           "elegibilidade": ("", *ELEGIVEL, "restrita", "nao_informada"),
           "candidatura": ("simplificada", "externa"),
           "status": ("", "aberta", "encerrada", "removida")}
CHAVES = {"titulo", "empresa", "link", "local", "data", "requisitos", "trecho", "evidencia", *VALORES}
OBRIGATORIAS = ("titulo", "empresa", "link")
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


def titulos_excluidos(cfg):
    """Campo opcional do busca.yaml; ausente ou vazio = não filtra. Aceita um valor só ou lista."""
    v = cfg.get("titulos_excluidos") or []
    return [v] if isinstance(v, str) else v


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
                if q["location"] in GEO_IDS:
                    q["geoId"] = GEO_IDS[q["location"]]
            q["f_TPR"] = f"r{segundos}"
            if wt:
                q["f_WT"] = wt
            q["sortBy"] = "DD"
            urls.append("https://www.linkedin.com/jobs/search/?" + urlencode(q))
    return urls


def _norm(s):
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def _sem_acento(s):
    return "".join(c for c in unicodedata.normalize("NFD", _norm(s)) if not unicodedata.combining(c))


def termo_no_titulo(titulo, termos):
    """Primeiro termo de `termos` que aparece no título como palavra inteira, sem acento e sem
    diferença de caixa (ex.: "Lead" casa "Tech Lead", não "Leadership"); None se nenhum."""
    t = _sem_acento(titulo)
    for termo in termos or ():
        n = _sem_acento(termo)
        if n and re.search(rf"(?<!\w){re.escape(n)}(?!\w)", t):
            return termo
    return None


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


def processar(vagas, excluidas_text, desde=None, hoje=None, remoto=False, maximo=None,
              titulos_excluidos=()):
    """Devolve (aceitas, descartadas). Descartada = {titulo, empresa, link, motivo}.
    remoto=True (regime remoto): exige modalidade remota verificada e que a vaga aceite candidatos
    do Brasil, da LATAM ou de qualquer lugar (campos "modalidade" e "elegibilidade").
    maximo: teto de vagas aceitas; as que passam das regras além dele são cortadas na ordem de coleta.
    titulos_excluidos: termos de nível (ex.: Staff, Principal) que descartam a vaga pelo título."""
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
        termo = termo_no_titulo(v.get("titulo"), titulos_excluidos)
        if termo:
            descarta(v, f"nível acima do alvo (título contém {termo!r})")
            continue
        status = _norm(v.get("status") or "aberta")
        if status != "aberta":
            descarta(v, f"não aceita mais candidaturas ({status})")
            continue
        if remoto:
            mod, ele = _norm(v.get("modalidade")), _norm(v.get("elegibilidade"))
            if not mod:
                descarta(v, "modalidade não verificada")
                continue
            if mod not in ("remoto", "remote"):
                descarta(v, f"não é remota ({mod})")
                continue
            if ele == "restrita":
                descarta(v, "restrita a candidatos de outro país")
                continue
            if ele not in ELEGIVEL:
                descarta(v, "não confirma aceitar candidatos do Brasil, LATAM ou de qualquer lugar")
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
        if maximo and len(out) >= maximo:
            descarta(v, f"acima do limite de {maximo} vagas (ordem de coleta)")
            continue
        if lk:
            vistos_link.add(lk)
        vistos_te.add(te)
        out.append(v)
    return out, fora


def filtros_extras(url):
    """Filtros que o LinkedIn aplicou além do pedido (ex.: f_SAL, que pode esconder vagas)."""
    q = parse_qs(urlsplit(url).query)
    return {k: v[0] for k, v in q.items() if k not in PARAMS_ESPERADOS}


def selecionar(itens, excluidas_text, por_url=POR_URL, total=TOTAL_CANDIDATOS):
    """Da listagem de todas as URLs ({origem, id, titulo, empresa, ...}, na ordem lida) ao que será
    aberto e verificado: em rodízio entre as URLs (nenhuma domina), no máximo por_url por URL e
    total no geral."""
    linhas = _excluidas_terms(excluidas_text)
    por_origem, vistos = {}, set()
    for it in itens:
        emp = _norm(it.get("empresa"))
        if it.get("id") in vistos or (emp and any(emp in l for l in linhas)):
            continue
        vistos.add(it.get("id"))
        por_origem.setdefault(it.get("origem"), []).append(it)
    filas = [iter(v[:por_url]) for v in por_origem.values()]
    out = []
    while filas and len(out) < total:
        for f in list(filas):
            it = next(f, None)
            if it is None:
                filas.remove(f)
            elif len(out) < total:
                out.append(it)
    return out


def validar_vagas(vagas):
    """Problemas do contrato skill -> script; lista vazia = JSON utilizável."""
    probs = []
    for i, v in enumerate(vagas, 1):
        probs += [f"vaga {i}: chave desconhecida ({k!r})" for k in v if k not in CHAVES]
        probs += [f"vaga {i}: falta {k}" for k in OBRIGATORIAS if not str(v.get(k) or "").strip()]
        for campo, aceitos in VALORES.items():
            valor = _norm(v.get(campo))
            if valor not in aceitos:
                probs.append(f"vaga {i}: {campo} inválido ({v.get(campo)!r}); aceitos: "
                             + ", ".join(a or "(vazio)" for a in aceitos))
    return probs


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
                  f"- Modalidade: {v.get('modalidade') or 'não verificada'} "
                  f"(aceita candidatos de: {v.get('elegibilidade') or 'não confirmado'})",
                  f"- Evidência: {v.get('evidencia') or 'não registrada'}",
                  f"- Candidatura: {chave}", f"- Link: {v.get('link', '')}",
                  f"- Trecho: {v.get('requisitos') or v.get('trecho', '')}", ""]
    if descartadas:
        L += ["# Descartadas", ""]
        L += [f"- {d['titulo']} | {d['empresa']} | {d['motivo']} | {d['link']}" for d in descartadas]
        L.append("")
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["urls", "candidatos", "filtros", "gravar"])
    ap.add_argument("--busca", default=str(ROOT / "busca.yaml"))
    ap.add_argument("--excluidas", default=str(ROOT / "private/perfil/vagas_excluidas.md"))
    ap.add_argument("--resultados")
    ap.add_argument("--listagens", help="JSON da listagem de todas as URLs (comando 'candidatos')")
    ap.add_argument("--url", help="URL final da página de busca (comando 'filtros')")
    ap.add_argument("--por-url", type=int, default=POR_URL)
    ap.add_argument("--total", type=int, default=TOTAL_CANDIDATOS)
    ap.add_argument("--saida-dir", default=str(ROOT / "private/vagas"))
    ap.add_argument("--data", default=date.today().isoformat())
    ap.add_argument("--desde", help="AAAA-MM-DD; padrão: data da última busca")
    ap.add_argument("--max", type=int, default=MAX_VAGAS, help=f"teto de vagas gravadas (padrão {MAX_VAGAS})")
    a = ap.parse_args(argv)
    probs = validar_config.validate(a.busca, a.excluidas)
    if probs:
        for p in probs:
            print(p, file=sys.stderr)
        print(f"Configuração incompleta ({len(probs)} problema(s)) ou de exemplo. /busca recusa rodar.",
              file=sys.stderr)
        return 1
    hoje = date.fromisoformat(a.data)
    cfg = parse_busca(Path(a.busca).read_text(encoding="utf-8"))
    desde = date.fromisoformat(a.desde) if a.desde else janela_desde(a.saida_dir, hoje)
    if a.cmd == "urls":
        print(f"desde {desde}")
        print("\n".join(build_urls(cfg, desde, hoje)))
        return 0
    if a.cmd == "filtros":
        if not a.url:
            print("--url é obrigatório em 'filtros' (a URL final, depois do redirecionamento)", file=sys.stderr)
            return 2
        extras = filtros_extras(a.url)
        print("\n".join(f"{k}={v}" for k, v in extras.items()) or "nenhum filtro extra")
        return 0
    if a.cmd == "candidatos":
        if not a.listagens or not Path(a.listagens).is_file():
            print("--listagens é obrigatório em 'candidatos' (arquivo JSON existente)", file=sys.stderr)
            return 2
        itens = json.loads(Path(a.listagens).read_text(encoding="utf-8"))
        termos = titulos_excluidos(cfg)
        for it in itens:  # corta antes da verificação: evita abrir uma página por vaga de nível acima
            termo = termo_no_titulo(it.get("titulo"), termos)
            if termo:
                print(f"descartada pelo título ({termo}): {it.get('titulo', '')} | {it.get('empresa', '')}",
                      file=sys.stderr)
        itens = [it for it in itens if not termo_no_titulo(it.get("titulo"), termos)]
        sel = selecionar(itens, Path(a.excluidas).read_text(encoding="utf-8"), a.por_url, a.total)
        print(json.dumps(sel, ensure_ascii=False, indent=1))
        return 0
    if not a.resultados:
        print("--resultados é obrigatório em 'gravar'", file=sys.stderr)
        return 2
    vagas = json.loads(Path(a.resultados).read_text(encoding="utf-8"))
    probs = validar_vagas(vagas)
    if probs:
        print("\n".join(probs), file=sys.stderr)
        print(f"{len(probs)} problema(s) no JSON de resultados; nada foi gravado.", file=sys.stderr)
        return 1
    final, fora = processar(vagas, Path(a.excluidas).read_text(encoding="utf-8"), desde, hoje,
                          remoto=_norm(cfg.get("regime")) == "remoto", maximo=a.max,
                          titulos_excluidos=titulos_excluidos(cfg))
    out = Path(a.saida_dir)
    out.mkdir(parents=True, exist_ok=True)
    dest = out / f"{a.data}-busca.md"
    dest.write_text(render(final, a.data, fora, desde), encoding="utf-8")
    print(f"{len(final)} vaga(s) gravada(s) em {dest}; {len(fora)} descartada(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
