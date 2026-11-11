"""Coleta de vagas pelas fontes de ATS (fontes_ats.json) no formato comum de processar().

Um adaptador por ATS (hoje: Greenhouse e Lever; Ashby e Himalayas entram depois, sem mexer nas
regras de descarte, que ficam em busca.processar()). O fetcher é injetável (seam único): em
produção é um GET público sem chave; nos testes, respostas gravadas. Só o token público vai na
URL; a descrição completa da vaga nunca é lida nem gravada. Falha de uma fonte (timeout, 404,
5xx, JSON inválido) vira entrada em "falhas" e a rodada segue. Pausa entre chamadas: 1 a 2 s.
"""
import json, random, re, time, unicodedata, urllib.error, urllib.request
from datetime import datetime, timezone

TIMEOUT = 15
PAUSA = (1.0, 2.0)  # segundos entre uma fonte e a seguinte
USER_AGENT = "job-hunt-coleta/1.0"
# Elegibilidade só pelo texto de localização; nunca "mundo" por suposição.
MARCAS_BRASIL = ("brasil", "brazil", "sao paulo", "rio de janeiro", "belo horizonte", "curitiba",
                 "porto alegre", "florianopolis", "recife", "brasilia", "campinas", "salvador",
                 "fortaleza", "vitoria", "goiania", "joinville", "londrina")
MARCAS_LATAM = ("latam", "latin america", "america latina", "latinoamerica")


def http_get(url):
    """Fetcher de produção: GET público, sem chave e sem dado pessoal."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read().decode("utf-8")


def _sem_acento(s):
    return "".join(c for c in unicodedata.normalize("NFD", (s or "").lower())
                   if not unicodedata.combining(c))


def _tem(texto, marcas):
    return any(re.search(rf"(?<!\w){re.escape(m)}(?!\w)", texto) for m in marcas)


def elegibilidade_do_local(local):
    """brasil | latam | nao_informada (remoto sem país, região desconhecida ou vazio)."""
    t = _sem_acento(local)
    if _tem(t, MARCAS_BRASIL):
        return "brasil"
    if _tem(t, MARCAS_LATAM):
        return "latam"
    return "nao_informada"


def modalidade_do_local(local):
    """remoto | hibrido | presencial, pelo texto de localização; vazio = não verificada."""
    t = _sem_acento(local)
    if _tem(t, ("remote", "remoto")):
        return "remoto"
    if _tem(t, ("hybrid", "hibrido")):
        return "hibrido"
    if _tem(t, ("on-site", "onsite", "on site", "presencial")):
        return "presencial"
    return ""


class Greenhouse:
    """API pública de lista de vagas: boards-api.greenhouse.io/v1/boards/{token}/jobs (sem content)."""
    ats = "greenhouse"

    @staticmethod
    def url(fonte):
        return f"https://boards-api.greenhouse.io/v1/boards/{fonte['token']}/jobs"

    @staticmethod
    def vagas(texto, fonte):
        jobs = json.loads(texto).get("jobs")
        if not isinstance(jobs, list):
            raise ValueError("resposta sem lista 'jobs'")
        out = []
        for j in jobs:
            if not (j.get("title") and j.get("absolute_url")):
                continue
            local = (j.get("location") or {}).get("name") or ""
            # first_published é a data de publicação; updated_at (atualização) não é usada.
            out.append({
                "titulo": j["title"], "empresa": fonte["empresa"], "link": j["absolute_url"],
                "local": local, "data": (j.get("first_published") or "")[:10],
                "requisitos": "", "evidencia": f"Localização no Greenhouse: {local or 'não informada'}",
                "fonte": f"{Greenhouse.ats}:{fonte['token']}", "candidatura": "externa", "status": "aberta",
                "modalidade": modalidade_do_local(local), "elegibilidade": elegibilidade_do_local(local),
            })
        return out


class Lever:
    """API pública de postings: api.lever.co/v0/postings/{token}?mode=json (sem chave).
    createdAt é epoch em ms (data de publicação); updatedAt não é usada. Uma página de até 100
    vagas por rodada (limit=100); a paginação por skip foi medida, mas não é seguida aqui."""
    ats = "lever"

    @staticmethod
    def url(fonte):
        return f"https://api.lever.co/v0/postings/{fonte['token']}?mode=json&limit=100"

    @staticmethod
    def vagas(texto, fonte):
        jobs = json.loads(texto)
        if not isinstance(jobs, list):
            raise ValueError("resposta sem lista de vagas")
        out = []
        for j in jobs:
            if not (j.get("text") and j.get("hostedUrl")):
                continue
            local = (j.get("categories") or {}).get("location") or ""
            criada = j.get("createdAt")
            data = datetime.fromtimestamp(criada / 1000, timezone.utc).date().isoformat() if criada else ""
            out.append({
                "titulo": j["text"], "empresa": fonte["empresa"], "link": j["hostedUrl"],
                "local": local, "data": data,
                "requisitos": "", "evidencia": f"Localização no Lever: {local or 'não informada'}",
                "fonte": f"{Lever.ats}:{fonte['token']}", "candidatura": "externa", "status": "aberta",
                "modalidade": modalidade_do_local(local), "elegibilidade": elegibilidade_do_local(local),
            })
        return out


ADAPTADORES = {a.ats: a for a in (Greenhouse, Lever)}


def _motivo(e):
    if isinstance(e, urllib.error.HTTPError):
        return f"HTTP {e.code}"
    if isinstance(e, urllib.error.URLError):
        return "erro de rede"
    if isinstance(e, TimeoutError):
        return "timeout"
    if isinstance(e, ValueError):
        return "resposta inválida (JSON)"
    return type(e).__name__


def coletar(fontes, fetch=http_get, pausa=PAUSA, sleep=time.sleep):
    """Devolve (vagas, falhas). Fonte cujo ATS não tem adaptador ainda é ignorada."""
    vagas, falhas, feitas = [], [], 0
    for fonte in fontes:
        adaptador = ADAPTADORES.get(fonte.get("ats"))
        if adaptador is None:
            continue
        if feitas:
            sleep(random.uniform(*pausa))
        feitas += 1
        try:
            vagas += adaptador.vagas(fetch(adaptador.url(fonte)), fonte)
        except Exception as e:  # uma fonte que falha não derruba a rodada
            falhas.append({"fonte": f"{fonte.get('ats')}:{fonte.get('token')}", "motivo": _motivo(e)})
    return vagas, falhas
