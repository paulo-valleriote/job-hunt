"""Adaptador do agregador Himalayas para o /busca (spec fontes-gratuitas-vagas, ticket 06).

Isolado de coleta.py: Himalayas não é ATS de token, então não entra em fontes_ats.json. A ativação
é fixa: o comando 'coletar' do busca.py chama coletar() uma vez por rodada e soma o resultado.

Semântica medida (GET público, sem chave, 2026-11-11):
- country=Brazil devolve vagas com "Brazil" em locationRestrictions e vagas com lista vazia
  (= worldwide): totalCount 5.835; amostra de 20 com 9 "Brazil" e 11 vazias; nenhuma só com outros países.
- worldwide=true combinado com country=Brazil NÃO soma: devolve só as 820 worldwide. Por isso a
  consulta usa só country=Brazil (worldwide já está dentro dela).
- Paginação: /jobs/api/search pagina por ?page=N (20 por página). O nextCursor só existe em
  /jobs/api (feed geral, sem filtro de país testado). Decisão: page=N, isolada em url().
- Data de publicação: pubDate (epoch em segundos). expiryDate = pubDate + 30 ou 60 dias na amostra,
  então pubDate é a publicação e não uma atualização. Não foi possível provar que pubDate nunca muda.

Elegibilidade por locationRestrictions: vazia = mundo; contém Brazil = brasil; só outros = restrita.
Gravado por vaga: metadados, link (applicationLink), atribuição "Fonte: Himalayas" e evidência
curta. Nunca description nem excerpt. Cache de 24 h em private/cache/himalayas.json (ignorado pelo
git), guardando só as vagas normalizadas; dentro da janela não há chamada à rede.
"""
import json, random, time, urllib.parse
from datetime import datetime, timezone
from pathlib import Path

import coleta

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://himalayas.app/jobs/api/search"
FILTROS = {"country": "Brazil"}
FONTE = "himalayas"
ATRIBUICAO = "Fonte: Himalayas"
JANELA_CACHE = 24 * 3600
MAX_PAGINAS = 5  # 100 vagas por rodada; a ordem de /search não foi medida, então o teto é fixo
PAUSA = (1.0, 2.0)
CACHE_ARQUIVO = ROOT / "private/cache/himalayas.json"


def url(pagina=1):
    params = dict(FILTROS)
    if pagina > 1:
        params["page"] = pagina
    return f"{BASE}?{urllib.parse.urlencode(params)}"


def elegibilidade(restricoes):
    if not restricoes:
        return "mundo"
    return "brasil" if "Brazil" in restricoes else "restrita"


def _evidencia(restricoes, el):
    if el == "mundo":
        return "locationRestrictions: [] (worldwide)"
    if el == "brasil":
        return 'locationRestrictions inclui "Brazil"'
    return "locationRestrictions sem Brazil: " + ", ".join(restricoes[:3])


def _data(epoch):
    if not isinstance(epoch, (int, float)):
        return ""
    return datetime.fromtimestamp(epoch, timezone.utc).date().isoformat()


def pagina(texto, agora):
    """Uma página crua -> (vagas normalizadas, totalCount, quantas vagas vieram).
    Levanta ValueError se não for JSON com lista 'jobs'."""
    d = json.loads(texto)
    jobs = d.get("jobs") if isinstance(d, dict) else None
    if not isinstance(jobs, list):
        raise ValueError("resposta sem lista 'jobs'")
    t = agora()
    out = []
    for j in jobs:
        if not (j.get("title") and j.get("applicationLink")):
            continue
        restricoes = j.get("locationRestrictions") or []
        el = elegibilidade(restricoes)
        exp = j.get("expiryDate")
        out.append({
            "titulo": j["title"], "empresa": j.get("companyName") or "", "link": j["applicationLink"],
            "local": {"brasil": "Remoto (Brasil)", "mundo": "Remoto (mundo)"}.get(el, "Remoto (restrito)"),
            "data": _data(j.get("pubDate")), "requisitos": "", "evidencia": _evidencia(restricoes, el),
            "fonte": FONTE, "atribuicao": ATRIBUICAO, "candidatura": "externa",
            "status": "encerrada" if isinstance(exp, (int, float)) and exp < t else "aberta",
            "modalidade": "remoto", "elegibilidade": el,
        })
    return out, d.get("totalCount") or 0, len(jobs)


def normalizar(texto, agora):
    """Só as vagas de uma página crua (mesmo contrato de pagina())."""
    return pagina(texto, agora)[0]


def _ler_cache(arquivo, agora):
    try:
        d = json.loads(Path(arquivo).read_text(encoding="utf-8"))
        gerado, vagas = float(d["gerado_em"]), d["vagas"]
    except (OSError, ValueError, KeyError, TypeError):
        return None
    if not isinstance(vagas, list) or not 0 <= agora() - gerado < JANELA_CACHE:
        return None
    return vagas


def _gravar_cache(arquivo, agora, vagas):
    try:
        Path(arquivo).parent.mkdir(parents=True, exist_ok=True)
        Path(arquivo).write_text(json.dumps({"gerado_em": agora(), "vagas": vagas}, ensure_ascii=False),
                                 encoding="utf-8")
    except OSError:
        pass  # cache é só economia de rede; falha de escrita não derruba a rodada


def coletar(fetch=coleta.http_get, pausa=PAUSA, sleep=time.sleep, agora=time.time,
            cache=CACHE_ARQUIVO, paginas=MAX_PAGINAS):
    """Devolve (vagas, falhas). Dentro de 24 h usa o cache e não chama a rede. Falha em uma página
    vira falha da fonte; o que já veio é mantido, mas não é gravado no cache."""
    cacheadas = _ler_cache(cache, agora)
    if cacheadas is not None:
        return cacheadas, []
    vagas, visto = [], 0
    for n in range(1, paginas + 1):
        if n > 1:
            sleep(random.uniform(*pausa))
        try:
            pv, total, bruto = pagina(fetch(url(n)), agora)
        except Exception as e:  # uma fonte que falha não derruba a rodada
            return vagas, [{"fonte": FONTE, "motivo": coleta._motivo(e)}]
        vagas += pv
        visto += bruto
        if bruto == 0 or visto >= total:
            break
    _gravar_cache(cache, agora, vagas)
    return vagas, []
