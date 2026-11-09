"""Testes da checagem anti-invenção (scripts/anti_invencao.py).
Seams: checar(resume, perfil_texto) -> lista de fatos sem respaldo; relatorio(); CLI
`checar <pasta> --perfil <arquivo>` (exit 1 e anti_invencao.md se houver fato sem respaldo).
Só dados fictícios em diretório temporário."""
import copy, json, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import anti_invencao as a  # noqa: E402

PERFIL = """# Perfil
## Experiência
### Acme Corp — Desenvolvedor Backend (2020-03 a 2023-06)
- Reduzi o tempo de resposta da API em 40% com cache em Redis.
- Mantive serviços em Python e Django com PostgreSQL.
## Formação
- Bacharelado em Ciência da Computação — Universidade Exemplo — concluído em 2019
## Certificações
- AWS Cloud Practitioner — Amazon — 2021
## Idiomas
- Português nativo; English advanced
"""

RESUME = {
    "basics": {"name": "Fulano de Tal", "label": "Desenvolvedor Backend",
               "summary": "Desenvolvedor backend com experiência em Python e Django."},
    "work": [{"name": "Acme Corp", "position": "Desenvolvedor Backend",
              "startDate": "2020-03", "endDate": "2023-06",
              "highlights": ["Reduzi o tempo de resposta da API em 40% com cache em Redis.",
                             "Mantive serviços em Python e Django com PostgreSQL."]}],
    "education": [{"institution": "Universidade Exemplo", "studyType": "Bacharelado",
                   "area": "Ciência da Computação", "endDate": "2019"}],
    "skills": [{"name": "Backend", "keywords": ["Python", "Django", "PostgreSQL", "Redis"]}],
    "certificates": [{"name": "AWS Cloud Practitioner", "issuer": "Amazon", "date": "2021"}],
    "languages": [{"language": "English", "fluency": "advanced"}],
}


def com(mut):
    r = copy.deepcopy(RESUME); mut(r); return r


class Checar(unittest.TestCase):
    def test_fiel_passa_sem_alarme(self):
        self.assertEqual(a.checar(RESUME, PERFIL), [])

    def test_metrica_inventada(self):
        r = com(lambda r: r["work"][0]["highlights"].append("Aumentei a receita em 300%."))
        achados = a.checar(r, PERFIL)
        self.assertTrue(any("300%" in x["fato"] or "300%" in x["motivo"] for x in achados))

    def test_tecnologia_inventada(self):
        r = com(lambda r: r["skills"][0]["keywords"].append("Kubernetes"))
        self.assertTrue(any("Kubernetes" in x["fato"] for x in a.checar(r, PERFIL)))

    def test_tecnologia_inventada_em_highlight(self):
        r = com(lambda r: r["work"][0]["highlights"].append("Orquestrei deploys com Terraform e Kafka."))
        fatos = " ".join(x["fato"] + x["motivo"] for x in a.checar(r, PERFIL))
        self.assertIn("Terraform", fatos); self.assertIn("Kafka", fatos)

    def test_cargo_inventado(self):
        r = com(lambda r: r["work"][0].update(position="Diretor de Engenharia"))
        self.assertTrue(any("Diretor" in x["fato"] for x in a.checar(r, PERFIL)))

    def test_empresa_inventada(self):
        r = com(lambda r: r["work"].append({"name": "Globex", "position": "Desenvolvedor Backend",
                                            "startDate": "2018-01", "endDate": "2019-12", "highlights": []}))
        self.assertTrue(any("Globex" in x["fato"] for x in a.checar(r, PERFIL)))

    def test_certificacao_inventada(self):
        r = com(lambda r: r["certificates"].append({"name": "CISSP", "issuer": "ISC2", "date": "2022"}))
        self.assertTrue(any("CISSP" in x["fato"] for x in a.checar(r, PERFIL)))

    def test_data_inventada(self):
        r = com(lambda r: r["work"][0].update(startDate="2017-01"))
        self.assertTrue(any("2017" in x["fato"] for x in a.checar(r, PERFIL)))

    def test_ignora_acentos_e_caixa(self):
        r = com(lambda r: r["education"][0].update(area="CIENCIA DA COMPUTACAO"))
        self.assertEqual(a.checar(r, PERFIL), [])

    def test_present_nao_e_data_inventada(self):
        r = com(lambda r: r["work"][0].update(endDate="Present"))
        self.assertEqual([x for x in a.checar(r, PERFIL) if "Present" in x["fato"]], [])


PERFIL_PT = """# Perfil
### Beta SA — Backend Engineer (2021-01 a atual)
- Node.js e APIs REST.
- Serviços de até 2.800 requisições por segundo, em mais de 25 ambientes. [medido]
- Reduzi logs de 4,5% para 3,0% do volume total. [medido]
- Plataforma com mais de R$ 100 mil em ativos.
- Microsserviços com comunicação assíncrona (SNS/SQS), sistemas distribuídos e WebSockets.
- Testes automatizados: unitários, de integração e E2E; testes de regressão; refatoração.
## Formação
- Tecnólogo em Sistemas de Computação — Universidade Exemplo — em andamento desde 2023-07.
## Certificações
AWS Certified Developer – Associate — Amazon — situação: [válida].
AWS Certified Cloud Practitioner — Amazon — situação: [expirada em 08/2026].
## Idiomas
- Português — nativo.
- Inglês — avançado
"""

RESUME_EN = {
    "basics": {"name": "Fulana", "label": "Backend Engineer",
               "summary": "Backend engineer using Node.js/SQS. Services reach up to 2,800 requests per second across 25+ environments."},
    "work": [{"name": "Beta SA", "position": "Backend Engineer", "startDate": "2021-01", "endDate": "Present",
              "highlights": ["Reduced logs from 4.5% to 3.0% of total volume on a platform with over R$ 100k in assets.",
                             "Built microservices with asynchronous communication (SNS/SQS) and WebSocket updates."]}],
    "education": [{"institution": "Universidade Exemplo", "studyType": "Technologist degree (in progress)",
                   "area": "Computer Systems", "startDate": "2023-07", "endDate": ""}],
    "skills": [{"name": "x", "keywords": ["Microservices", "Distributed systems", "Unit tests", "Integration tests",
                                          "E2E tests", "Regression tests", "Refactoring", "REST APIs"]}],
    "certificates": [{"name": "AWS Certified Developer – Associate (valid)", "issuer": "Amazon", "date": ""},
                     {"name": "AWS Certified Cloud Practitioner (expired 08/2026)", "issuer": "Amazon", "date": ""}],
    "languages": [{"language": "Portuguese", "fluency": "Native"}, {"language": "English", "fluency": "Advanced"}],
}


def en(mut):
    r = copy.deepcopy(RESUME_EN); mut(r); return r


class InglesSobrePerfilEmPortugues(unittest.TestCase):
    def test_traducao_fiel_passa(self):
        self.assertEqual(a.checar(RESUME_EN, PERFIL_PT), [])

    def test_numeros_em_outro_formato_passam(self):
        self.assertEqual(a._canon_numeros("2,800 e 2.800 e 4.5% e 4,5% e 100k e 100 mil e 25+"),
                         "2800 e 2800 e 4.5% e 4.5% e 100000 e 100000 e 25")

    def test_numero_alterado_reprova(self):
        for troca in ("2,800", "25+", "4.5%", "100k"):
            novo = {"2,800": "3,800", "25+": "40+", "4.5%": "5.5%", "100k": "900k"}[troca]
            def mut(r, a_=troca, b_=novo):
                r["basics"]["summary"] = r["basics"]["summary"].replace(a_, b_)
                r["work"][0]["highlights"][0] = r["work"][0]["highlights"][0].replace(a_, b_)
            self.assertTrue(a.checar(en(mut), PERFIL_PT), troca)

    def test_certificacao_com_situacao_trocada_reprova(self):
        r = en(lambda r: r["certificates"][1].update(name="AWS Certified Cloud Practitioner (valid)"))
        self.assertTrue(any("situação" in x["motivo"] for x in a.checar(r, PERFIL_PT)))

    def test_certificacao_com_data_errada_reprova(self):
        r = en(lambda r: r["certificates"][1].update(name="AWS Certified Cloud Practitioner (expired 01/2026)"))
        self.assertTrue(any("situação" in x["motivo"] for x in a.checar(r, PERFIL_PT)))

    def test_certificacao_inexistente_com_situacao_reprova(self):
        r = en(lambda r: r["certificates"].append({"name": "CISSP (valid)", "issuer": "Amazon", "date": ""}))
        self.assertTrue(any("CISSP" in x["fato"] for x in a.checar(r, PERFIL_PT)))

    def test_traducao_sem_termo_no_perfil_reprova(self):
        perfil = PERFIL_PT.replace("Microsserviços", "Serviços")
        self.assertTrue(any(x["fato"] == "Microservices" for x in a.checar(RESUME_EN, perfil)))

    def test_composto_com_parte_inventada_reprova(self):
        r = en(lambda r: r["basics"].update(summary="Backend engineer using Node.js/Kubernetes daily."))
        self.assertTrue(any("Kubernetes" in x["motivo"] for x in a.checar(r, PERFIL_PT)))

    def test_idioma_nao_listado_reprova(self):
        r = en(lambda r: r["languages"].append({"language": "German", "fluency": "Fluent"}))
        self.assertTrue(any("German" in x["fato"] for x in a.checar(r, PERFIL_PT)))

    def test_formacao_inventada_reprova(self):
        r = en(lambda r: r["education"][0].update(studyType="PhD"))
        self.assertTrue(any("PhD" in x["fato"] for x in a.checar(r, PERFIL_PT)))


PERFIL_MIN = """# Perfil
## Experiência
### Acme Corp — Desenvolvedor Backend (2020-03 a 2023-06)
- Mantive serviços em Python.
## Formação
- Bacharelado em Ciência da Computação — Universidade Exemplo — concluído em 2019
## Certificações
- AWS Cloud Practitioner — Amazon — 2021 — situação: [válida].
## Idiomas
- Português nativo.
"""

RESUME_MIN = {
    "basics": {"name": "Fulano", "label": "Desenvolvedor Backend", "summary": "Backend com Python."},
    "work": [{"name": "Acme Corp", "position": "Desenvolvedor Backend", "startDate": "2020-03",
              "endDate": "2023-06", "highlights": ["Mantive serviços em Python."]}],
    "education": [{"institution": "Universidade Exemplo", "studyType": "Bacharelado",
                   "area": "Ciência da Computação", "endDate": "2019"}],
    "skills": [{"name": "x", "keywords": ["Python"]}],
    "certificates": [{"name": "AWS Cloud Practitioner (valid)", "issuer": "Amazon", "date": "2021"}],
    "languages": [{"language": "Portuguese", "fluency": "Native"}],
}


def min_(mut):
    r = copy.deepcopy(RESUME_MIN); mut(r); return r


class Omissoes(unittest.TestCase):
    def test_perfil_minimo_completo_passa(self):
        self.assertEqual(a.omissoes(RESUME_MIN, PERFIL_MIN), [])

    def test_empresa_faltando_reprova(self):
        r = min_(lambda r: r.update(work=[]))
        self.assertTrue(any("Acme Corp" in x["fato"] for x in a.omissoes(r, PERFIL_MIN)))

    def test_cargo_faltando_reprova(self):
        r = min_(lambda r: r["work"][0].update(position="Diretor"))
        self.assertTrue(any("Desenvolvedor Backend" in x["motivo"] for x in a.omissoes(r, PERFIL_MIN)))

    def test_periodo_faltando_reprova(self):
        r = min_(lambda r: r["work"][0].update(startDate="2021-01"))
        self.assertTrue(a.omissoes(r, PERFIL_MIN))

    def test_formacao_faltando_reprova(self):
        r = min_(lambda r: r.update(education=[]))
        self.assertTrue(any("Universidade Exemplo" in x["fato"] for x in a.omissoes(r, PERFIL_MIN)))

    def test_certificacao_faltando_reprova(self):
        r = min_(lambda r: r.update(certificates=[]))
        self.assertTrue(any("Cloud Practitioner" in x["fato"] for x in a.omissoes(r, PERFIL_MIN)))

    def test_perfil_sem_estrutura_levanta_erro(self):
        with self.assertRaises(a.PerfilSemEstrutura):
            a.omissoes(RESUME_MIN, "# Perfil\n## Experiência\nsem nada estruturado\n")

    def test_formacao_sem_separador_em_travessao_levanta_erro(self):
        perfil = PERFIL_MIN.replace("- Bacharelado em Ciência da Computação — Universidade Exemplo — concluído em 2019",
                                    "- Universidade Exemplo, Bacharelado, 2019")
        with self.assertRaises(a.PerfilSemEstrutura):
            a.omissoes(RESUME_MIN, perfil)

    def test_en_pt_fiel_nao_reprova(self):
        self.assertEqual(a.omissoes(RESUME_EN, PERFIL_PT), [])

    def test_en_pt_certificacao_omitida_reprova(self):
        r = en(lambda r: r.update(certificates=[r["certificates"][0]]))
        self.assertTrue(any("Cloud Practitioner" in x["fato"] for x in a.omissoes(r, PERFIL_PT)))

    def test_cli_empresa_faltando_sai_1_e_relata(self):
        d = tempfile.TemporaryDirectory(); self.addCleanup(d.cleanup)
        pasta = Path(d.name) / "cv"; pasta.mkdir()
        (pasta / "resume.json").write_text(json.dumps(min_(lambda r: r.update(work=[]))), encoding="utf-8")
        perfil = Path(d.name) / "profile_truth.md"; perfil.write_text(PERFIL_MIN, encoding="utf-8")
        self.assertEqual(a.main(["checar", str(pasta), "--perfil", str(perfil)]), 1)
        md = (pasta / "anti_invencao.md").read_text(encoding="utf-8")
        self.assertIn("## Omissões", md)
        self.assertIn("Acme Corp", md.split("## Omissões")[1])

    def test_cli_perfil_sem_estrutura_sai_2(self):
        d = tempfile.TemporaryDirectory(); self.addCleanup(d.cleanup)
        pasta = Path(d.name) / "cv"; pasta.mkdir()
        (pasta / "resume.json").write_text(json.dumps(RESUME_MIN), encoding="utf-8")
        perfil = Path(d.name) / "profile_truth.md"; perfil.write_text("# vazio\n", encoding="utf-8")
        self.assertEqual(a.main(["checar", str(pasta), "--perfil", str(perfil)]), 2)


PERFIL_NI = PERFIL_MIN + """## Termos proibidos
- RabbitMQ
- Go
- Kubernetes
"""


class TermosProibidos(unittest.TestCase):
    def test_termo_presente_reprova(self):
        r = min_(lambda r: r["work"][0]["highlights"].append("Operei RabbitMQ em produção."))
        achados, avisos = a.termos_proibidos(r, PERFIL_NI)
        self.assertTrue(any("RabbitMQ" in x["motivo"] for x in achados))
        self.assertEqual(avisos, [])

    def test_termo_ausente_passa(self):
        achados, avisos = a.termos_proibidos(RESUME_MIN, PERFIL_NI)
        self.assertEqual(achados, [])

    def test_palavra_contida_em_outra_nao_reprova(self):
        r = min_(lambda r: r["basics"].update(summary="Experiência com Google Cloud e Python."))
        achados, _ = a.termos_proibidos(r, PERFIL_NI)
        self.assertFalse(any("Go" in x["motivo"] for x in achados))

    def test_comparacao_ignora_caixa_e_acento(self):
        r = min_(lambda r: r["basics"].update(summary="uso kubernetes no dia a dia."))
        achados, _ = a.termos_proibidos(r, PERFIL_NI)
        self.assertTrue(achados)

    def test_secao_ausente_avisa_sem_bloquear(self):
        achados, avisos = a.termos_proibidos(RESUME_MIN, PERFIL_MIN)
        self.assertEqual(achados, [])
        self.assertTrue(avisos)

    def test_secao_vazia_avisa_sem_bloquear(self):
        achados, avisos = a.termos_proibidos(RESUME_MIN, PERFIL_MIN + "## Termos proibidos\n\n")
        self.assertEqual(achados, [])
        self.assertTrue(avisos)

    def test_comentario_de_exemplo_nao_conta_como_termo(self):
        perfil = PERFIL_MIN + "## Termos proibidos\n<!-- exemplo: Kubernetes -->\n- RabbitMQ\n"
        r = min_(lambda r: r["skills"][0]["keywords"].append("Kubernetes"))
        achados, _ = a.termos_proibidos(r, perfil)
        self.assertEqual(achados, [])

    def test_comentario_de_varias_linhas_nao_vira_termo(self):
        perfil = PERFIL_MIN + "## Termos proibidos\n<!-- Um termo\nGo\n-->\n- RabbitMQ\n"
        achados, avisos = a.termos_proibidos(RESUME_MIN, perfil)
        self.assertEqual(achados, [])
        self.assertEqual(avisos, [])
        r = min_(lambda r: r["basics"].update(summary="Um termo Go"))
        self.assertEqual(a.termos_proibidos(r, perfil)[0], [])

    def test_cli_termo_presente_sai_1_e_secao_propria(self):
        d = tempfile.TemporaryDirectory(); self.addCleanup(d.cleanup)
        pasta = Path(d.name) / "cv"; pasta.mkdir()
        r = min_(lambda r: r["work"][0]["highlights"].append("Operei RabbitMQ."))
        (pasta / "resume.json").write_text(json.dumps(r), encoding="utf-8")
        perfil = Path(d.name) / "profile_truth.md"; perfil.write_text(PERFIL_NI, encoding="utf-8")
        self.assertEqual(a.main(["checar", str(pasta), "--perfil", str(perfil)]), 1)
        md = (pasta / "anti_invencao.md").read_text(encoding="utf-8")
        self.assertIn("## Termos proibidos", md)
        self.assertIn("RabbitMQ", md.split("\n## Termos proibidos\n")[1])


class Cli(unittest.TestCase):
    def roda(self, resume):
        d = tempfile.TemporaryDirectory(); self.addCleanup(d.cleanup)
        pasta = Path(d.name) / "cv"; pasta.mkdir()
        (pasta / "resume.json").write_text(json.dumps(resume), encoding="utf-8")
        perfil = Path(d.name) / "profile_truth.md"; perfil.write_text(PERFIL, encoding="utf-8")
        rc = a.main(["checar", str(pasta), "--perfil", str(perfil)])
        return rc, pasta

    def test_fiel_exit0_e_relatorio(self):
        rc, pasta = self.roda(RESUME)
        self.assertEqual(rc, 0)
        self.assertIn("Nenhum fato sem respaldo", (pasta / "anti_invencao.md").read_text(encoding="utf-8"))

    def test_inventado_bloqueia_e_relata(self):
        rc, pasta = self.roda(com(lambda r: r["skills"][0]["keywords"].append("Kubernetes")))
        self.assertEqual(rc, 1)
        self.assertIn("Kubernetes", (pasta / "anti_invencao.md").read_text(encoding="utf-8"))

    def test_sem_opcao_de_desativar(self):
        with self.assertRaises(SystemExit):
            a.main(["checar", "x", "--perfil", "y", "--desligar"])

    def test_resume_ausente(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(a.main(["checar", d, "--perfil", d]), 2)


if __name__ == "__main__":
    unittest.main()
