"""Adaptador do Catálogo Rebase: o único módulo que fala com a API (https://rebasedev.com.br/api/v1).

Interface pública:
  coletar(config, token, fetch, sleep) -> {vagas, falhas, descartadas}
      config = {"skills": [slugs]} (stack já traduzida); fetch(url, headers) devolve o corpo em texto
      e lança HTTPError para status de erro; sleep(s) espera. Lê até 10 páginas (ou até a última).
  ler_token(arquivo) -> str | None   (linha TOKEN= de private/rebase.env)
  traduzir_stack(lista) -> [slugs]   (normalização sem caixa, acento e pontuação, mais apelidos)
  http_get(url, headers) e motivo_da_falha(e): também usados pela coleta antiga (coleta.py).

Só leitura. O token nunca entra em motivo, log ou saída. Vagas com apply_url nulo e de nível acima
do alvo (sênior, staff, liderança) saem em "descartadas" com motivo; os filtros de janela, título e
vagas_excluidas.md são aplicados depois, em busca.processar().
"""
import json, re, time, unicodedata, urllib.error, urllib.parse, urllib.request
from pathlib import Path

BASE = "https://rebasedev.com.br/api/v1"
ENV_ARQUIVO = Path(__file__).resolve().parent.parent / "private" / "rebase.env"
TIMEOUT = 15
USER_AGENT = "job-hunt-rebase/1.0"
POR_PAGINA = 50
MAX_PAGINAS = 10
ESPERA_MAX = 60  # segundos: 429 com Retry-After acima disso vira falha de fonte
ACEITE_URL = "https://rebasedev.com.br/jobs/perfil/aceite"
TOKEN_URL = "https://rebasedev.com.br/jobs/perfil/agentes"
# Nível acima do alvo, sem acento (seniority vem com acento; a comparação ignora o acento).
NIVEIS_DESCARTADOS = {"senior", "staff", "lideranca"}
# Apelidos de stack: chave já normalizada -> slug do Rebase. Pontuação e caixa saem na normalização
# ("Node.js" vira "nodejs" sem apelido).
APELIDOS = {"golang": "go", "node": "nodejs", "postgresql": "postgres", "k8s": "kubernetes"}
MODELOS = {"pj": "PJ", "clt": "CLT", "eor": "EOR"}
PERIODOS = {"YEAR": "ano", "MONTH": "mês", "HOUR": "hora"}


def _sem_acento(s):
    return "".join(c for c in unicodedata.normalize("NFD", (s or "").lower()) if not unicodedata.combining(c))


def _chave(s):
    return re.sub(r"[^a-z0-9]", "", _sem_acento(s))


def traduzir_stack(stack):
    """Lista de nomes (do stack_desejada) -> slugs de skill, sem repetidos e na ordem de entrada."""
    out = []
    for nome in stack or []:
        k = _chave(nome)
        if not k:
            continue
        slug = APELIDOS.get(k, k)
        if slug not in out:
            out.append(slug)
    return out


def ler_token(arquivo=ENV_ARQUIVO):
    """Valor da linha TOKEN= (não REBASE_TOKEN). Arquivo ausente ou valor vazio = None."""
    try:
        linhas = Path(arquivo).read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    for linha in linhas:
        m = re.match(r"^\s*TOKEN\s*=\s*(.*?)\s*$", linha)
        if m:
            valor = m.group(1).strip("'\"")
            return valor or None
    return None


def http_get(url, headers=None):
    """Fetcher de produção: GET com os headers dados (Authorization, no caso do Rebase)."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json",
                                               **(headers or {})})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read().decode("utf-8")


def motivo_da_falha(e):
    if isinstance(e, urllib.error.HTTPError):
        return f"HTTP {e.code}"
    if isinstance(e, urllib.error.URLError):
        return "erro de rede"
    if isinstance(e, TimeoutError):
        return "timeout"
    if isinstance(e, ValueError):
        return "resposta inválida (JSON)"
    return type(e).__name__


def _motivo_http(e):
    if isinstance(e, urllib.error.HTTPError):
        if e.code == 401:
            return f"token recusado (401): gere outro em {TOKEN_URL}"
        if e.code == 403:
            return f"aceite de Novidades ausente (403): {ACEITE_URL}"
        if e.code == 429:
            return "limite de taxa (429)"
    return motivo_da_falha(e)


def _espera(e):
    try:
        return float(e.headers.get("Retry-After"))
    except (TypeError, ValueError, AttributeError):
        return None


def _buscar_pagina(url, token, fetch, sleep):
    """Uma página; 429 com Retry-After <= ESPERA_MAX espera e tenta a mesma página uma única vez."""
    headers = {"Authorization": f"Bearer {token}"}
    repetiu = False
    while True:
        try:
            return json.loads(fetch(url, headers))
        except urllib.error.HTTPError as e:
            espera = _espera(e) if e.code == 429 else None
            if e.code == 429 and not repetiu and espera is not None and espera <= ESPERA_MAX:
                sleep(espera)
                repetiu = True
                continue
            raise


def _nivel_descartado(nivel):
    return _sem_acento(nivel).strip() in NIVEIS_DESCARTADOS


def _trecho(j):
    partes = []
    modelos = [MODELOS.get(str(m).lower(), str(m)) for m in (j.get("hiring_models") or [])]
    if modelos:
        partes.append(", ".join(modelos))
    lo, hi, moeda = j.get("salary_min"), j.get("salary_max"), j.get("salary_currency")
    if lo is not None and hi is not None and moeda:
        periodo = PERIODOS.get(str(j.get("salary_interval") or ""), "")
        partes.append(f"{moeda} {lo}–{hi}" + (f"/{periodo}" if periodo else ""))
    return " · ".join(partes)


def _traduzir(j):
    """Vaga do Rebase -> (registro, None) ou (None, descarte com motivo)."""
    link = j.get("apply_url")
    empresa = (j.get("company") or {}).get("name") or ""
    titulo = j.get("title") or ""
    if not link:
        return None, {"titulo": titulo, "empresa": empresa, "link": j.get("url") or "",
                      "motivo": "sem apply_url (candidatura no ATS)"}
    if _nivel_descartado(j.get("seniority")):
        return None, {"titulo": titulo, "empresa": empresa, "link": link,
                      "motivo": f"nível acima do alvo ({j.get('seniority')})"}
    local = j.get("location") or ""
    reqs = [str(s) for s in (j.get("skills_principais") or [])]
    return {
        "titulo": titulo, "empresa": empresa, "link": link, "atribuicao": j.get("url") or "",
        "local": local, "modalidade": "remoto", "elegibilidade": "brasil",
        "evidencia": f"Rebase: contrata quem mora no Brasil ({local or 'não informada'})",
        "data": (j.get("first_seen_at") or "")[:10],
        "requisitos": ("Requer: " + ", ".join(reqs)) if reqs else "",
        "trecho": _trecho(j), "status": "aberta", "candidatura": "externa", "fonte": "rebase",
    }, None


def _url(skills, pagina):
    params = [("por_pagina", POR_PAGINA), ("pagina", pagina)] + [("skill", s) for s in skills]
    return f"{BASE}/jobs?" + urllib.parse.urlencode(params)


def coletar(config, token, fetch=http_get, sleep=time.sleep):
    """Devolve {vagas, falhas, descartadas}. Falha de leitura mantém as páginas já lidas e diz em
    que página a leitura parou; o token não aparece em nenhum motivo."""
    skills = list(config.get("skills") or [])
    vagas, falhas, descartadas = [], [], []
    pagina = 1
    while pagina <= MAX_PAGINAS:
        try:
            corpo = _buscar_pagina(_url(skills, pagina), token, fetch, sleep)
            itens = corpo["data"]
            if not isinstance(itens, list):
                raise ValueError("data sem lista")
            meta = corpo.get("meta") or {}
        except Exception as e:  # uma falha de fonte não derruba a rodada
            falhas.append({"fonte": "rebase",
                           "motivo": f"{_motivo_http(e)}; leitura parou na página {pagina}"})
            break
        for j in itens:
            vaga, descarte = _traduzir(j)
            if vaga:
                vagas.append(vaga)
            else:
                descartadas.append(descarte)
        ultima = not itens or int(meta.get("pagina", pagina)) >= int(meta.get("paginas", pagina))
        if ultima:
            break
        pagina += 1
    return {"vagas": vagas, "falhas": falhas, "descartadas": descartadas}


# --- Configuração e diagnóstico (check-config e doctor). Funções novas, no fim do arquivo. ---

def mensagem_token_ausente():
    """Instrução exata para quem não tem TOKEN= em private/rebase.env (check-config e doctor)."""
    return f"gere o token em {TOKEN_URL} e grave TOKEN= em private/rebase.env"


def buscar_skills_meta(fetch=http_get, base=BASE):
    """Slugs de skill aceitos pela API, de GET /api/v1/meta (aberta, sem token): {data: {skills: [...]}}.
    Aceita item como objeto com "slug" ou como texto."""
    corpo = json.loads(fetch(f"{base}/meta", {}))
    itens = (corpo.get("data") or {}).get("skills") or []
    slugs = {(i.get("slug") if isinstance(i, dict) else str(i)) for i in itens}
    return {s for s in slugs if s}


def checar_token(token, base=BASE, fetch=http_get):
    """Uma única chamada GET /jobs?por_pagina=1 autenticada -> (ok, texto). O token nunca entra no texto."""
    try:
        json.loads(fetch(f"{base}/jobs?por_pagina=1", {"Authorization": f"Bearer {token}"}))
        return True, "ok"
    except Exception as e:
        if isinstance(e, urllib.error.HTTPError) and e.code == 401:
            return False, f"token recusado (401): gere outro em {TOKEN_URL}"
        if isinstance(e, urllib.error.HTTPError) and e.code == 403:
            return False, f"sem aceite (403): {ACEITE_URL}"
        return False, _motivo_http(e)
