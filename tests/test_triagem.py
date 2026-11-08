"""Testes do /triagem (scripts/triagem.py).
Seams: preflight() (gate), classificar_entrada(), caminho_triagem(), validar_saida() e a CLI.
Só fixtures fictícias em diretório temporário; sem rede, sem vendor/, sem private/ real."""
import subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
import triagem as t  # noqa: E402
from tests.test_validar_config import BUSCA_OK, EXC_OK  # noqa: E402

SAIDA_OK = """\
# Triagem: Acme Corp, Dev Backend
Nota de aderência: 7.5/10

## Motivos
- Python consta no perfil.

## Lacunas
- Kubernetes: exigido pela vaga, não consta no perfil.
"""


def montar(d, busca=BUSCA_OK, exc=EXC_OK, perfil="# Perfil fictício\n"):
    d = Path(d)
    (d / "busca.yaml").write_text(busca, encoding="utf-8")
    (d / "exc.md").write_text(exc, encoding="utf-8")
    if perfil is not None:
        (d / "profile_truth.md").write_text(perfil, encoding="utf-8")
    return d / "busca.yaml", d / "exc.md", d / "profile_truth.md"


class Preflight(unittest.TestCase):
    def test_config_completa_passa(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(t.preflight(*montar(d)), [])

    def test_placeholders_bloqueiam(self):
        with tempfile.TemporaryDirectory() as d:
            probs = t.preflight(*montar(d, busca=BUSCA_OK.replace("pleno", "EXEMPLO pleno")))
            self.assertTrue(any("senioridade" in str(p) for p in probs))

    def test_sem_profile_truth_bloqueia(self):
        with tempfile.TemporaryDirectory() as d:
            probs = t.preflight(*montar(d, perfil=None))
            self.assertTrue(any("profile_truth" in str(p) for p in probs))


class Entrada(unittest.TestCase):
    def test_link(self):
        self.assertEqual(t.classificar_entrada("https://x.com/job/1"), "link")

    def test_texto(self):
        self.assertEqual(t.classificar_entrada("Vaga de Dev\nRequisitos: Python"), "texto")

    def test_link_com_texto_ao_redor_e_texto(self):
        self.assertEqual(t.classificar_entrada("veja https://x.com/1 e a vaga pede Go"), "texto")

    def test_vazio(self):
        self.assertEqual(t.classificar_entrada("  "), "vazio")


class Caminho(unittest.TestCase):
    def test_slug_e_data(self):
        p = t.caminho_triagem(Path("v"), "2026-11-08", "Acme Corp", "Dev Backend Sênior")
        self.assertEqual(p, Path("v/2026-11-08-triagem-acme-corp-dev-backend-senior.md"))


class Saida(unittest.TestCase):
    def test_ok(self):
        self.assertEqual(t.validar_saida(SAIDA_OK), [])

    def test_sem_nota(self):
        self.assertTrue(t.validar_saida(SAIDA_OK.replace("Nota de aderência: 7.5/10", "")))

    def test_nota_fora_da_faixa(self):
        self.assertTrue(t.validar_saida(SAIDA_OK.replace("7.5/10", "11/10")))

    def test_sem_lacunas(self):
        self.assertTrue(t.validar_saida(SAIDA_OK.split("## Lacunas")[0]))

    def test_lacunas_vazias(self):
        self.assertTrue(t.validar_saida(SAIDA_OK.split("- Kubernetes")[0]))


class Cli(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(ROOT / "scripts/triagem.py"), *args],
                              capture_output=True, text=True)

    def test_check_recusa_com_placeholder(self):
        with tempfile.TemporaryDirectory() as d:
            b, e, p = montar(d, busca=BUSCA_OK.replace("remoto", "EXEMPLO remoto"))
            r = self.run_cli("check", "--busca", str(b), "--excluidas", str(e), "--perfil", str(p))
            self.assertEqual(r.returncode, 1)
            self.assertIn("regime", r.stderr)

    def test_check_ok(self):
        with tempfile.TemporaryDirectory() as d:
            b, e, p = montar(d)
            r = self.run_cli("check", "--busca", str(b), "--excluidas", str(e), "--perfil", str(p))
            self.assertEqual(r.returncode, 0, r.stderr)

    def test_salvar_valida_e_grava(self):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "saida.md"
            src.write_text(SAIDA_OK, encoding="utf-8")
            r = self.run_cli("salvar", str(src), "--vagas", d, "--data", "2026-11-08",
                             "--empresa", "Acme", "--cargo", "Dev")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertTrue((Path(d) / "2026-11-08-triagem-acme-dev.md").is_file())

    def test_salvar_recusa_saida_invalida(self):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "saida.md"
            src.write_text("sem estrutura", encoding="utf-8")
            r = self.run_cli("salvar", str(src), "--vagas", d, "--data", "2026-11-08",
                             "--empresa", "A", "--cargo", "B")
            self.assertEqual(r.returncode, 1)
            self.assertEqual([f for f in Path(d).glob("*triagem*")], [])


if __name__ == "__main__":
    unittest.main()
