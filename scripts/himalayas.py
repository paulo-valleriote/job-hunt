"""Adaptador do agregador Himalayas para o /busca (spec fontes-gratuitas-vagas, ticket 06).

Isolado de coleta.py: Himalayas não é ATS de token, então não entra em fontes_ats.json. A ativação
é fixa: o comando 'coletar' do busca.py chama coletar() uma vez por rodada e soma o resultado.

Consultas (duas, em sequência, cada uma paginada): country=Brazil e worldwide=true. As vagas são
unidas e deduplicadas pelo link sem query string. Só os parâmetros country, worldwide e page são
enviados (nada pessoal).

Semântica medida (GET público, sem chave, 2026-11-11):
- country=Brazil devolve vagas com "Brazil" em locationRestrictions e vagas com lista vazia
  (= worldwide): totalCount 5.835; amostra de 20 com 9 "Brazil" e 11 vazias; nenhuma só com outros países.
- worldwide=true sozinho: totalCount 820, todas com locationRestrictions vazia. Na primeira página,
  só 11 de 20 já estão na primeira página de country=Brazil, então a união acrescenta vagas.
- worldwide=true combinado com country=Brazil NÃO soma: devolve só as 820 worldwide (medido antes).
  Por isso as duas consultas são separadas e unidas no código.
- Ordenação: sort=recent é aceito mas a resposta é idêntica à padrão (não ordena). sort=date,
  sort=newest, sort=pubDate e sort=latest devolvem 400 "Invalid sort". Não há parâmetro de ordenação
  por data. A ordem da página é só aproximada (página 1 mistura datas de 11/11 a 17/10; página 2 de
  country=Brazil vem de 11/11 para 10/11). Por isso a coleta ordena o resultado por pubDate
  decrescente no código, e a paginação para ao encontrar uma página sem vaga dentro da janela `desde`.
- Paginação: ?page=N (20 por página). O nextCursor só aparece em /jobs/api (feed geral, sem filtro).
- Data de publicação: pubDate (epoch em segundos). expiryDate = pubDate + 30 ou 60 dias na amostra,
  então pubDate é a publicação e não uma atualização. Não foi possível provar que pubDate nunca muda.

Elegibilidade por locationRestrictions: vazia = mundo; contém Brazil = brasil; só outros = restrita.
Gravado por vaga: metadados, link (applicationLink), atribuição "Fonte: Himalayas" e evidência
curta. Nunca description nem excerpt. Cache de 24 h em private/cache/himalayas.json (ignorado pelo
git), com chave que inclui as consultas, o teto de páginas e a janela `desde`; dentro da janela não
há chamada à rede.
"""
import json, random, time, urllib.parse
from datetime import date, datetime, timezone
from pathlib import Path

import coleta

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://himalayas.app/jobs/api/search"
FILTROS = ({"country": "Brazil"}, {"worldwide": "true"})  # consultas separadas, unidas por link
FONTE = "himalayas"
ATRIBUICAO = "Fonte: Himalayas"
JANELA_CACHE = 24 * 3600
MAX_PAGINAS = 5  # 100 vagas por consulta e por rodada (são 2 consultas)
PAUSA = (1.0, 2.0)
CACHE_ARQUIVO = ROOT / "private/cache/himalayas.json"


def url(pagina=1, filtro=FILTROS[0]):
    params = dict(filtro)
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
        if not (j.get("title") and j.get("applicationLink") and j.get("companyName")):
            continue  # sem empresa, validar_vagas derrubaria o gravar inteiro
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


def _chave_link(link):
    return (link or "").split("?", 1)[0]


def _chave(paginas, desde):
    """Identifica a rodada: quem muda o conteúdo do cache (consultas, teto, janela) muda a chave."""
    return json.dumps({"consultas": FILTROS, "paginas": paginas,
                       "desde": desde.isoformat() if desde else None}, sort_keys=True)


def _ler_cache(arquivo, agora, chave):
    try:
        d = json.loads(Path(arquivo).read_text(encoding="utf-8"))
        gerado, vagas = float(d["gerado_em"]), d["vagas"]
    except (OSError, ValueError, KeyError, TypeError):
        return None
    if d.get("chave") != chave or not isinstance(vagas, list) or not 0 <= agora() - gerado < JANELA_CACHE:
        return None
    return vagas


def _gravar_cache(arquivo, agora, chave, vagas):
    try:
        Path(arquivo).parent.mkdir(parents=True, exist_ok=True)
        Path(arquivo).write_text(json.dumps({"gerado_em": agora(), "chave": chave, "vagas": vagas},
                                            ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass  # cache é só economia de rede; falha de escrita não derruba a rodada


def coletar(fetch=coleta.http_get, pausa=PAUSA, sleep=time.sleep, agora=time.time,
            cache=CACHE_ARQUIVO, paginas=MAX_PAGINAS, desde=None):
    """Devolve (vagas, falhas), mais recentes primeiro. `desde` (date) é a início da janela: a
    paginação de cada consulta para na primeira página sem nenhuma vaga com data >= desde.
    Dentro de 24 h, com a mesma chave, usa o cache e não chama a rede. Falha em uma página vira
    falha da fonte e a consulta seguinte continua; com falha, nada vai para o cache."""
    chave = _chave(paginas, desde)
    cacheadas = _ler_cache(cache, agora, chave)
    if cacheadas is not None:
        return cacheadas, []
    vagas, falhas, vistos, feitas = [], [], set(), 0
    limite = desde.isoformat() if desde else None
    for filtro in FILTROS:
        visto = 0
        for n in range(1, paginas + 1):
            if feitas:
                sleep(random.uniform(*pausa))
            feitas += 1
            try:
                pv, total, bruto = pagina(fetch(url(n, filtro)), agora)
            except Exception as e:  # uma fonte que falha não derruba a rodada
                falhas.append({"fonte": FONTE, "motivo": coleta.motivo_da_falha(e)})
                break
            for v in pv:
                k = _chave_link(v["link"])
                if k not in vistos:  # união das consultas: a primeira ocorrência fica
                    vistos.add(k)
                    vagas.append(v)
            visto += bruto
            if bruto == 0 or visto >= total:
                break
            if limite and not any(v["data"] and v["data"] >= limite for v in pv):
                break  # página inteira fora da janela: as seguintes tendem a ser mais antigas
    vagas.sort(key=lambda v: v["data"] or "", reverse=True)  # sort é estável: empates mantêm a ordem
    if not falhas:
        _gravar_cache(cache, agora, chave, vagas)
    return vagas, falhas
