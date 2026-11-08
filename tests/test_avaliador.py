"""Testes do ciclo avaliador/revisão (scripts/avaliador.py).
Seams: validar_avaliacao(), decidir(), finalizar() (pasta temporária com versões fictícias) e a CLI."""
import json, os, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import avaliador as a  # noqa: E402

AV = {"nota": 7, "pontos_fortes": ["Python"], "lacunas": ["Kubernetes"], "palavras_chave": ["python", "api"]}


def versao(pasta, n, nota, marca=None):
    d = Path(pasta) / "versoes" / f"v{n}"
    d.mkdir(parents=True)
    (d / "resume.json").write_text(json.dumps({"marca": marca or f"v{n}"}))
    (d / "avaliacao.json").write_text(json.dumps({**AV, "nota": nota}))


class Validar(unittest.TestCase):
    def test_ok(self):
        self.assertEqual(a.validar_avaliacao(AV), [])

    def test_nota_fora_da_faixa(self):
        self.assertTrue(a.validar_avaliacao({**AV, "nota": 11}))
        self.assertTrue(a.validar_avaliacao({**AV, "nota": 0.5}))

    def test_campo_ausente(self):
        d = dict(AV); del d["lacunas"]
        self.assertTrue(a.validar_avaliacao(d))


class Decidir(unittest.TestCase):
    def test_primeira_nota_baixa_revisa(self):
        self.assertEqual(a.decidir([7.0]), ("revisar", ""))

    def test_alvo_atingido_para(self):
        self.assertEqual(a.decidir([8.5])[0], "parar")
        self.assertIn("alvo", a.decidir([9.0])[1])

    def test_melhorou_continua(self):
        self.assertEqual(a.decidir([6, 7])[0], "revisar")

    def test_nao_melhorou_para(self):
        acao, motivo = a.decidir([7, 7])
        self.assertEqual(acao, "parar"); self.assertIn("melhor", motivo)
        self.assertEqual(a.decidir([7, 6])[0], "parar")

    def test_maximo_de_revisoes(self):
        self.assertEqual(a.decidir([5, 6, 7])[0], "revisar")
        acao, motivo = a.decidir([5, 6, 7, 8])
        self.assertEqual(acao, "parar"); self.assertIn("máximo", motivo)

    def test_teto_configuravel(self):
        self.assertEqual(a.decidir([5, 6], max_rev=1)[0], "parar")

    def test_melhor_nota_previa_conta(self):
        # 7 -> 8 -> 7.5: não melhorou sobre a melhor (8)
        self.assertEqual(a.decidir([7, 8, 7.5])[0], "parar")


class Finalizar(unittest.TestCase):
    def test_entrega_a_de_melhor_nota_nao_a_ultima(self):
        with tempfile.TemporaryDirectory() as d:
            versao(d, 1, 6); versao(d, 2, 8); versao(d, 3, 7)
            r = a.finalizar(d)
            self.assertEqual(r, 2)
            self.assertEqual(json.loads((Path(d) / "resume.json").read_text())["marca"], "v2")
            rep = (Path(d) / "rating_report.md").read_text()
            for s in ("v1", "v2", "v3", "Entregue: v2", "Motivo da parada"):
                self.assertIn(s, rep)

    def test_empate_entrega_a_mais_antiga(self):
        with tempfile.TemporaryDirectory() as d:
            versao(d, 1, 7); versao(d, 2, 7)
            self.assertEqual(a.finalizar(d), 1)

    def test_sem_versoes(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                a.finalizar(d)


class Cli(unittest.TestCase):
    def run_cli(self, *args, env=None):
        return subprocess.run([sys.executable, str(ROOT / "scripts/avaliador.py"), *args],
                              capture_output=True, text=True, env={**os.environ, **(env or {})})

    def test_decidir_e_teto_por_env(self):
        with tempfile.TemporaryDirectory() as d:
            versao(d, 1, 5); versao(d, 2, 6)
            self.assertEqual(self.run_cli("decidir", d).stdout.split(":")[0].strip(), "revisar")
            r = self.run_cli("decidir", d, env={"JOBHUNT_MAX_REVISOES": "1"})
            self.assertTrue(r.stdout.startswith("parar"))

    def test_validar_cli(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "av.json"; f.write_text(json.dumps({**AV, "nota": 99}))
            self.assertEqual(self.run_cli("validar", str(f)).returncode, 1)
            f.write_text(json.dumps(AV))
            self.assertEqual(self.run_cli("validar", str(f)).returncode, 0)

    def test_finalizar_cli(self):
        with tempfile.TemporaryDirectory() as d:
            versao(d, 1, 6)
            self.assertEqual(self.run_cli("finalizar", d).returncode, 0)
            self.assertTrue((Path(d) / "rating_report.md").is_file())


if __name__ == "__main__":
    unittest.main()
