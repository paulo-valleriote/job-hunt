"""Coleta de vagas pelas fontes de ATS (fontes_ats.json) no formato comum de processar().

Um adaptador por ATS (hoje: Greenhouse; Lever, Ashby e Himalayas entram depois, sem mexer nas
regras de descarte, que ficam em busca.processar()). O fetcher é injetável (seam único): em
produção é um GET público sem chave; nos testes, respostas gravadas. Só o token público vai na
URL; a descrição completa da vaga nunca é lida nem gravada. Falha de uma fonte (timeout, 404,
5xx, JSON inválido) vira entrada em "falhas" e a rodada segue. Pausa entre chamadas: 1 a 2 s.
"""
import json, random, re, time, unicodedata, urllib.error, urllib.request

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


MODALIDADE_ASHBY = {"remote": "remoto", "hybrid": "hibrido", "onsite": "presencial"}


def _pais_do_endereco(endereco):
    if not isinstance(endereco, dict) or not isinstance(endereco.get("postalAddress"), dict):
        return None
    return endereco["postalAddress"].get("addressCountry") or None


class Ashby:
    """API pública de vagas publicadas: api.ashbyhq.com/posting-api/job-board/{board} (sem descrição).

    Elegibilidade: país dos campos estruturados (address e secondaryLocations) é sinal mais forte
    que o texto do local; só com campo estruturado ausente vale o texto. Não há país comprovável
    = nao_informada (descartada por elegibilidade). Data: publishedAt (updatedAt não é usada).
    """
    ats = "ashby"

    @staticmethod
    def url(fonte):
        return f"https://api.ashbyhq.com/posting-api/job-board/{fonte['token']}"

    @staticmethod
    def vagas(texto, fonte):
        jobs = json.loads(texto).get("jobs")
        if not isinstance(jobs, list):
            raise ValueError("resposta sem lista 'jobs'")
        out = []
        for j in jobs:
            if not (j.get("title") and j.get("jobUrl")):
                continue
            local = j.get("location") or ""
            paises = []  # (campo literal, país) dos campos estruturados, primário antes dos secundários
            if (p := _pais_do_endereco(j.get("address"))):
                paises.append(("addressCountry", p))
            for s in j.get("secondaryLocations") or []:
                if isinstance(s, dict) and (p := _pais_do_endereco(s.get("address"))):
                    paises.append(("secondaryLocations.addressCountry", p))
            brasil = [(c, p) for c, p in paises if _sem_acento(p).strip() in ("brazil", "brasil")]
            if brasil:
                elegibilidade, evidencia = "brasil", f"{brasil[0][0]}: {brasil[0][1]}"
            elif paises:
                elegibilidade, evidencia = "nao_informada", f"{paises[0][0]}: {paises[0][1]}"
            else:
                elegibilidade = elegibilidade_do_local(local)
                evidencia = f"location: {local or 'não informada'}"
            modalidade = MODALIDADE_ASHBY.get(str(j.get("workplaceType") or "").lower())
            if modalidade is None:
                modalidade = "remoto" if j.get("isRemote") is True else modalidade_do_local(local)
            out.append({
                "titulo": j["title"], "empresa": fonte["empresa"], "link": j["jobUrl"],
                "local": local, "data": (j.get("publishedAt") or "")[:10],
                "requisitos": "", "evidencia": evidencia,
                "fonte": f"{Ashby.ats}:{fonte['token']}", "candidatura": "externa", "status": "aberta",
                "modalidade": modalidade, "elegibilidade": elegibilidade,
            })
        return out


ADAPTADORES = {a.ats: a for a in (Greenhouse, Ashby)}


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
