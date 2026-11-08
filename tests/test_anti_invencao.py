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
