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
- Universidade Exemplo, Bacharelado em Ciência da Computação, 2019
## Certificações
- AWS Cloud Practitioner (Amazon), 2021
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
