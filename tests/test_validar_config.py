"""Testes do gate de configuração (scripts/validar_config.py).
Seams: validate() (lista de problemas) e a CLI (código de saída + mensagem).
Só fixtures fictícias em diretório temporário."""
import subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import validar_config as v  # noqa: E402

BUSCA_OK = """\
cargos_alvo:
  - Engenheiro de Software Backend
senioridade: pleno
regime: remoto
paises_fuso:
  - Brasil
faixa_salarial_minima: 9000
stack_desejada:
  - Python
deal_breakers:
  - Plantão 24h
idiomas_aceitos:
  - pt-BR
  - en
"""
EXC_OK = """\
# Vagas excluídas
- 2026-10-01 | Acme Corp | presencial em Curitiba | motivo: salário
"""


def write(d, name, text):
    p = Path(d) / name
    p.write_text(text, encoding="utf-8")
    return p


class Gate(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.d = self.t.name

    def tearDown(self):
        self.t.cleanup()

    def run_validate(self, busca, exc):
        return v.validate(write(self.d, "busca.yaml", busca),
                          write(self.d, "vagas_excluidas.md", exc))

    def test_configuracao_valida_sem_problemas(self):
        self.assertEqual(self.run_validate(BUSCA_OK, EXC_OK), [])

    def test_placeholders_em_vagas_excluidas_com_linha(self):
        exc = "# x\n- AAAA-MM-DD | Empresa A | remoto\n- Recrutadora C\n"
        probs = self.run_validate(BUSCA_OK, exc)
        linhas = sorted({p.line for p in probs if p.path.name == "vagas_excluidas.md"})
        self.assertEqual(linhas, [2, 3])

    def test_modalidade_sem_cidade(self):
        exc = "- 2026-10-01 | Acme | presencial | motivo\n"
        probs = self.run_validate(BUSCA_OK, exc)
        self.assertEqual([p.line for p in probs], [1])

    def test_campo_vazio_em_busca(self):
        probs = self.run_validate(BUSCA_OK.replace("senioridade: pleno", "senioridade:"), EXC_OK)
        self.assertEqual([(p.path.name, p.line) for p in probs], [("busca.yaml", 3)])

    def test_lista_vazia_e_valor_de_exemplo(self):
        b = BUSCA_OK.replace("  - Python", "  - EXEMPLO Python")
        b = b.replace("  - Plantão 24h\n", "")
        linhas = sorted(p.line for p in self.run_validate(b, EXC_OK))
        self.assertEqual(linhas, [9, 10])

    def test_campo_ausente(self):
        b = BUSCA_OK.replace("regime: remoto\n", "")
        probs = self.run_validate(b, EXC_OK)
        self.assertEqual(len(probs), 1)
        self.assertIn("regime", probs[0].message)

    def test_arquivo_inexistente(self):
        probs = v.validate(Path(self.d) / "nao.yaml", Path(self.d) / "nao.md")
        self.assertEqual(len(probs), 2)

    def test_cli_recusa_com_arquivo_e_linha(self):
        b = write(self.d, "busca.yaml", BUSCA_OK.replace("pleno", ""))
        e = write(self.d, "vagas_excluidas.md", EXC_OK)
        r = subprocess.run([sys.executable, str(ROOT / "scripts/validar_config.py"),
                            "--busca", str(b), "--excluidas", str(e)],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)
        self.assertIn("busca.yaml:3:", r.stderr)

    def test_cli_ok(self):
        b = write(self.d, "busca.yaml", BUSCA_OK)
        e = write(self.d, "vagas_excluidas.md", EXC_OK)
        r = subprocess.run([sys.executable, str(ROOT / "scripts/validar_config.py"),
                            "--busca", str(b), "--excluidas", str(e)],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0)

    def test_modelo_do_repo_e_recusado(self):
        probs = v.validate(ROOT / "busca.example.yaml", Path(self.d) / "x.md")
        self.assertTrue([p for p in probs if p.path.name == "busca.example.yaml"])


if __name__ == "__main__":
    unittest.main()
