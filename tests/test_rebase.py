"""Adaptador do Catálogo Rebase (scripts/rebase.py) sem rede: fetch e sleep falsos, token de arquivo temporário.

Nunca usa private/, token real nem a API de verdade. Respostas são dicionários no formato do contrato
(envelope {data, meta}); os valores esperados vêm da spec, não do código.
"""
import json, sys, tempfile, unittest, urllib.error
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import rebase as rb  # noqa: E402

TOKEN_FAKE = "tok-de-teste-123"


def job(i, **kw):
    base = {
        "slug": f"vaga-{i}", "title": f"Backend Engineer {i}", "company": {"name": f"Empresa {i}", "slug": f"e{i}"},
        "location": "Remote (Worldwide)", "hires_in_brazil": "yes", "remoto_comprovado": True,
        "seniority": "pleno", "skills_principais": ["go", "aws"], "skills": ["go", "aws", "docker"],
        "hiring_models": ["pj"], "salary": None, "salary_min": None, "salary_max": None,
        "salary_currency": None, "salary_interval": None,
        "published_at": "2026-11-20T10:00:00.000+00:00", "first_seen_at": "2026-11-21T09:00:00.000+00:00",
        "apply_url": f"https://jobs.ashbyhq.com/acme/{i}", "url": f"https://rebasedev.com.br/jobs/vaga-{i}",
    }
    base.update(kw)
    return base


def pagina(jobs, n, total_paginas):
    return json.dumps({"data": jobs, "meta": {"total": 999, "pagina": n, "paginas": total_paginas,
                                               "por_pagina": 50}})


class Rede:
    """fetch falso: respostas indexadas pelo parâmetro `pagina` da URL; Exception é lançada."""

    def __init__(self, respostas):
        self.respostas = respostas  # {n_pagina: texto | Exception}
        self.chamadas = []  # (url, headers)

    def __call__(self, url, headers=None):
        self.chamadas.append((url, dict(headers or {})))
        n = int(parse_qs(urlsplit(url).query)["pagina"][0])
        r = self.respostas.get(n)
        if r is None:
            raise AssertionError(f"página {n} não deveria ter sido pedida")
        if isinstance(r, Exception):
            raise r
        return r


def http(code, headers=None):
    return urllib.error.HTTPError("https://rebasedev.com.br/api/v1/jobs", code, "x", headers or {}, None)


class Pausas:
    def __init__(self):
        self.esperas = []

    def __call__(self, s):
        self.esperas.append(s)


def coletar(rede, skills=("go",), pausas=None):
    r = rb.coletar({"skills": list(skills)}, TOKEN_FAKE, fetch=rede, sleep=pausas or Pausas())
    return r["vagas"], r["falhas"]


class Consulta(unittest.TestCase):
    def test_pede_bearer_por_pagina_e_skill_repetido_sem_filtros_proibidos(self):
        rede = Rede({1: pagina([], 1, 1)})
        coletar(rede, skills=("go", "typescript", "nodejs", "aws"))
        url, headers = rede.chamadas[0]
        q = parse_qs(urlsplit(url).query)
        self.assertTrue(url.startswith("https://rebasedev.com.br/api/v1/jobs?"))
        self.assertEqual(headers.get("Authorization"), f"Bearer {TOKEN_FAKE}")
        self.assertEqual(q["por_pagina"], ["50"])
        self.assertEqual(q["skill"], ["go", "typescript", "nodejs", "aws"])
        for proibido in ("q", "nivel", "modelo", "minhas_skills", "onde", "titulo"):
            self.assertNotIn(proibido, q)

    def test_para_na_ultima_pagina(self):
        rede = Rede({1: pagina([job(1)], 1, 2), 2: pagina([job(2)], 2, 2)})
        vagas, falhas = coletar(rede)
        self.assertEqual(len(rede.chamadas), 2)
        self.assertEqual(falhas, [])
        self.assertEqual([v["titulo"] for v in vagas], ["Backend Engineer 1", "Backend Engineer 2"])

    def test_para_na_decima_pagina_mesmo_com_mais_paginas(self):
        rede = Rede({n: pagina([job(n)], n, 20) for n in range(1, 11)})
        coletar(rede)
        self.assertEqual(len(rede.chamadas), 10)


class Traducao(unittest.TestCase):
    def traduz(self, **kw):
        vagas, _ = coletar(Rede({1: pagina([job(1, **kw)], 1, 1)}))
        return vagas[0]

    def test_campos_fixos_e_de_link(self):
        v = self.traduz()
        self.assertEqual(v["link"], "https://jobs.ashbyhq.com/acme/1")
        self.assertEqual(v["atribuicao"], "https://rebasedev.com.br/jobs/vaga-1")
        self.assertEqual((v["modalidade"], v["elegibilidade"]), ("remoto", "brasil"))
        self.assertEqual((v["status"], v["candidatura"], v["fonte"]), ("aberta", "externa", "rebase"))
        self.assertEqual(v["empresa"], "Empresa 1")
        self.assertEqual(v["local"], "Remote (Worldwide)")
        self.assertEqual(v["evidencia"], "Rebase: contrata quem mora no Brasil (Remote (Worldwide))")

    def test_data_vem_de_first_seen_at(self):
        self.assertEqual(self.traduz()["data"], "2026-11-21")

    def test_requisitos_vem_de_skills_principais(self):
        self.assertEqual(self.traduz()["requisitos"], "Requer: go, aws")

    def test_requisitos_vazio_sem_skills(self):
        self.assertEqual(self.traduz(skills_principais=[])["requisitos"], "")

    def test_trecho_com_modelo_e_salario_numerico(self):
        v = self.traduz(hiring_models=["pj"], salary_min=5000, salary_max=7000,
                        salary_currency="USD", salary_interval="MONTH")
        self.assertEqual(v["trecho"], "PJ · USD 5000–7000/mês")

    def test_trecho_so_com_modelo(self):
        self.assertEqual(self.traduz(hiring_models=["clt"])["trecho"], "CLT")

    def test_trecho_vazio_sem_modelo_nem_salario(self):
        self.assertEqual(self.traduz(hiring_models=[])["trecho"], "")

    def test_nivel_null_fica(self):
        vagas, _ = coletar(Rede({1: pagina([job(1, seniority=None)], 1, 1)}))
        self.assertEqual(len(vagas), 1)

    def test_nivel_junior_e_pleno_ficam(self):
        vagas, _ = coletar(Rede({1: pagina([job(1, seniority="júnior"), job(2, seniority="pleno")], 1, 1)}))
        self.assertEqual(len(vagas), 2)


class Descartes(unittest.TestCase):
    def coletar_com(self, *jobs):
        return rb.coletar({"skills": ["go"]}, TOKEN_FAKE, fetch=Rede({1: pagina(list(jobs), 1, 1)}),
                          sleep=Pausas())

    def test_sem_apply_url_e_descartada_com_motivo(self):
        r = self.coletar_com(job(1, apply_url=None))
        self.assertEqual(r["vagas"], [])
        self.assertEqual(r["falhas"], [])
        self.assertEqual(len(r["descartadas"]), 1)
        self.assertIn("apply_url", r["descartadas"][0]["motivo"])

    def test_niveis_acima_do_alvo_sao_descartados_com_nivel_acentuado(self):
        for nivel in ("sênior", "staff", "liderança"):
            with self.subTest(nivel=nivel):
                r = self.coletar_com(job(1, seniority=nivel))
                self.assertEqual(r["vagas"], [])
                self.assertEqual(r["descartadas"][0]["motivo"], f"nível acima do alvo ({nivel})")


class Erros(unittest.TestCase):
    def test_401_vira_falha_com_instrucao_e_mantem_paginas_lidas(self):
        rede = Rede({1: pagina([job(1)], 1, 3), 2: http(401)})
        vagas, falhas = coletar(rede)
        self.assertEqual(len(vagas), 1)
        self.assertEqual(len(falhas), 1)
        self.assertEqual(falhas[0]["fonte"], "rebase")
        self.assertIn("token recusado (401)", falhas[0]["motivo"])
        self.assertIn("https://rebasedev.com.br/jobs/perfil/agentes", falhas[0]["motivo"])
        self.assertIn("página 2", falhas[0]["motivo"])

    def test_403_vira_falha_com_link_do_aceite(self):
        _, falhas = coletar(Rede({1: http(403)}))
        self.assertIn("aceite de Novidades ausente (403)", falhas[0]["motivo"])
        self.assertIn("https://rebasedev.com.br/jobs/perfil/aceite", falhas[0]["motivo"])

    def test_5xx_rede_e_json_invalido_sem_nova_tentativa(self):
        casos = [(http(500), "HTTP 500"), (urllib.error.URLError("x"), "erro de rede"),
                 (TimeoutError(), "timeout"), ("{nao json", "resposta inválida (JSON)")]
        for resposta, esperado in casos:
            with self.subTest(esperado=esperado):
                rede = Rede({1: resposta})
                _, falhas = coletar(rede)
                self.assertIn(esperado, falhas[0]["motivo"])
                self.assertEqual(len(rede.chamadas), 1)

    def test_429_com_retry_after_curto_espera_e_repete_a_mesma_pagina_uma_vez(self):
        rede = Rede({1: http(429, {"Retry-After": "7"})})
        respostas = iter([http(429, {"Retry-After": "7"}), pagina([job(1)], 1, 1)])

        class Sequencia(Rede):
            def __call__(self, url, headers=None):
                self.chamadas.append((url, dict(headers or {})))
                r = next(respostas)
                if isinstance(r, Exception):
                    raise r
                return r

        seq = Sequencia({})
        pausas = Pausas()
        r = rb.coletar({"skills": ["go"]}, TOKEN_FAKE, fetch=seq, sleep=pausas)
        vagas, falhas = r["vagas"], r["falhas"]
        self.assertEqual(pausas.esperas, [7])
        self.assertEqual(len(seq.chamadas), 2)
        self.assertEqual(seq.chamadas[0][0], seq.chamadas[1][0])
        self.assertEqual(len(vagas), 1)
        self.assertEqual(falhas, [])

    def test_429_repetido_vira_falha(self):
        respostas = iter([http(429, {"Retry-After": "3"}), http(429, {"Retry-After": "3"})])

        class Sempre(Rede):
            def __call__(self, url, headers=None):
                self.chamadas.append((url, {}))
                raise next(respostas)

        pausas = Pausas()
        falhas = rb.coletar({"skills": ["go"]}, TOKEN_FAKE, fetch=Sempre({}), sleep=pausas)["falhas"]
        self.assertEqual(pausas.esperas, [3])
        self.assertIn("429", falhas[0]["motivo"])

    def test_429_com_espera_acima_de_60_vira_falha_sem_esperar(self):
        pausas = Pausas()
        rede = Rede({1: http(429, {"Retry-After": "61"})})
        falhas = rb.coletar({"skills": ["go"]}, TOKEN_FAKE, fetch=rede, sleep=pausas)["falhas"]
        self.assertEqual(pausas.esperas, [])
        self.assertEqual(len(rede.chamadas), 1)
        self.assertIn("429", falhas[0]["motivo"])

    def test_token_nunca_aparece_em_motivo_nem_em_saida(self):
        _, falhas = coletar(Rede({1: http(401)}))
        self.assertNotIn(TOKEN_FAKE, json.dumps(falhas, ensure_ascii=False))


class Token(unittest.TestCase):
    def test_le_a_linha_token_de_arquivo(self):
        with tempfile.TemporaryDirectory() as d:
            arq = Path(d) / "rebase.env"
            arq.write_text(f"OUTRA=1\nTOKEN={TOKEN_FAKE}\n", encoding="utf-8")
            self.assertEqual(rb.ler_token(arq), TOKEN_FAKE)

    def test_ignora_rebase_token_e_aceita_so_TOKEN(self):
        with tempfile.TemporaryDirectory() as d:
            arq = Path(d) / "rebase.env"
            arq.write_text(f"REBASE_TOKEN={TOKEN_FAKE}\n", encoding="utf-8")
            self.assertIsNone(rb.ler_token(arq))

    def test_arquivo_ausente_ou_linha_vazia_e_none(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertIsNone(rb.ler_token(Path(d) / "nao-existe.env"))
            arq = Path(d) / "rebase.env"
            arq.write_text("TOKEN=\n", encoding="utf-8")
            self.assertIsNone(rb.ler_token(arq))


class Stack(unittest.TestCase):
    def test_normalizacao_sem_caixa_acento_e_pontuacao(self):
        self.assertEqual(rb.traduzir_stack(["Go", "TypeScript", "AWS"]), ["go", "typescript", "aws"])
        self.assertEqual(rb.traduzir_stack(["Node.js"]), ["nodejs"])

    def test_apelidos(self):
        self.assertEqual(rb.traduzir_stack(["Golang"]), ["go"])

    def test_remove_repetidos_mantendo_a_ordem(self):
        self.assertEqual(rb.traduzir_stack(["Golang", "Go", "AWS"]), ["go", "aws"])


class ReusoNoModuloAntigo(unittest.TestCase):
    def test_http_get_e_motivo_da_falha_moram_no_adaptador(self):
        import coleta
        self.assertIs(coleta.motivo_da_falha, rb.motivo_da_falha)
        self.assertIs(coleta.http_get, rb.http_get)


META_JSON = json.dumps({"data": {"skills": [{"slug": "go"}, {"slug": "nodejs"}, {"slug": "python"}]}})


class Meta(unittest.TestCase):
    def test_lista_skills_do_meta_sem_token(self):
        chamadas = []

        def fetch(url, headers=None):
            chamadas.append((url, dict(headers or {})))
            return META_JSON

        self.assertEqual(rb.buscar_skills_meta(fetch=fetch), {"go", "nodejs", "python"})
        self.assertTrue(chamadas[0][0].endswith("/api/v1/meta"))
        self.assertNotIn("Authorization", chamadas[0][1])


class Doctor(unittest.TestCase):
    def checar(self, resposta):
        chamadas = []

        def fetch(url, headers=None):
            chamadas.append((url, dict(headers or {})))
            if isinstance(resposta, Exception):
                raise resposta
            return resposta

        return rb.checar_token(TOKEN_FAKE, fetch=fetch), chamadas

    def test_200_e_ok_com_uma_chamada_so(self):
        (ok, msg), chamadas = self.checar(json.dumps({"data": [], "meta": {}}))
        self.assertTrue(ok)
        self.assertEqual(msg, "ok")
        self.assertEqual(len(chamadas), 1)
        url, headers = chamadas[0]
        self.assertIn("por_pagina=1", url)
        self.assertIn("/jobs?", url)
        self.assertEqual(headers.get("Authorization"), f"Bearer {TOKEN_FAKE}")

    def test_401_e_token_recusado(self):
        (ok, msg), _ = self.checar(http(401))
        self.assertFalse(ok)
        self.assertIn("token recusado (401)", msg)

    def test_403_e_sem_aceite(self):
        (ok, msg), _ = self.checar(http(403))
        self.assertFalse(ok)
        self.assertIn("sem aceite (403)", msg)

    def test_outras_falhas_nao_sao_ok_e_nao_mostram_token(self):
        for e in (http(500), urllib.error.URLError("x"), ValueError("json")):
            (ok, msg), _ = self.checar(e)
            self.assertFalse(ok)
            self.assertNotIn(TOKEN_FAKE, msg)

    def test_mensagem_de_token_ausente_traz_instrucao(self):
        m = rb.mensagem_token_ausente()
        self.assertIn("https://rebasedev.com.br/jobs/perfil/agentes", m)
        self.assertIn("grave TOKEN= em private/rebase.env", m)


if __name__ == "__main__":
    unittest.main()
