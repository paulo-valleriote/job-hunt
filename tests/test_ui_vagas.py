"""Testes da lógica da tela Vagas (ui/vagas_core.py), sem Streamlit.
Seams: ultima_busca(), triagens(), ler_triagem(), triar() com runner injetado.
Só dados fictícios em diretório temporário; sem rede, sem claude real, sem private/ real."""
import sys, tempfile, time, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "ui"))
import vagas_core as v  # noqa: E402
from tests.test_triagem import SAIDA_OK  # noqa: E402
from scripts import busca as b  # noqa: E402


class Busca(unittest.TestCase):
    def test_sem_busca_retorna_none(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertIsNone(v.ultima_busca(d))

    def test_pega_a_mais_recente_e_le_o_formato_do_busca_py(self):
        with tempfile.TemporaryDirectory() as d:
            ds = [{"titulo": "Dev Py", "empresa": "Acme", "link": "https://x.test/1", "data": "2026-01-02", "trecho": "t"}]
            (Path(d) / "2026-01-01-busca.md").write_text(b.render([], "2026-01-01"))
            (Path(d) / "2026-01-02-busca.md").write_text(b.render(ds, "2026-01-02"))
            r = v.ultima_busca(d)
            self.assertEqual(r["data"], "2026-01-02")
            self.assertEqual(r["vagas"][0]["titulo"], "Dev Py")
            self.assertEqual(r["vagas"][0]["empresa"], "Acme")
            self.assertEqual(r["vagas"][0]["link"], "https://x.test/1")

    def test_le_grupos_e_ignora_descartadas(self):
        with tempfile.TemporaryDirectory() as d:
            ds = [{"titulo": "Ext", "empresa": "A", "link": "https://x.test/1", "data": "2026-01-02",
                   "candidatura": "externa", "requisitos": "Go"},
                  {"titulo": "Simp", "empresa": "B", "link": "https://x.test/2", "data": "2026-01-02"}]
            fora = [{"titulo": "Velha", "empresa": "Z", "link": "https://x.test/9", "motivo": "duplicada"}]
            (Path(d) / "2026-01-02-busca.md").write_text(b.render(ds, "2026-01-02", fora))
            r = v.ultima_busca(d)
            self.assertEqual([x["titulo"] for x in r["vagas"]], ["Simp", "Ext"])
            self.assertEqual(r["vagas"][1]["link"], "https://x.test/1")
            self.assertEqual(r["vagas"][1]["trecho"], "Go")


class Triagem(unittest.TestCase):
    def test_ler_triagem(self):
        r = v.ler_triagem(SAIDA_OK)
        self.assertEqual(r["nota"], 7.5)
        self.assertIn("Python", r["motivos"])
        self.assertIn("Kubernetes", r["lacunas"])

    def test_triar_chama_claude_p_com_o_comando_e_devolve_triagem_nova(self):
        with tempfile.TemporaryDirectory() as d:
            chamadas = []

            def runner(cmd):
                chamadas.append(cmd)
                (Path(d) / "2026-01-02-triagem-acme-dev.md").write_text(SAIDA_OK)
                return 0, ""
            r = v.triar("https://x.test/1", d, runner=runner)
            self.assertEqual(chamadas[0][:2], ["claude", "-p"])
            self.assertEqual(chamadas[0][2], "/triagem https://x.test/1")
            self.assertEqual(r["nota"], 7.5)

    def test_entrada_vazia_nao_chama_claude(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                v.triar("   ", d, runner=lambda c: self.fail("não deveria chamar"))

    def test_falha_do_claude_vira_erro(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(v.TriagemFalhou):
                v.triar("texto da vaga", d, runner=lambda c: (1, "gate recusou"))

    def test_sem_arquivo_novo_vira_erro_com_saida(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(v.TriagemFalhou) as cm:
                v.triar("texto", d, runner=lambda c: (0, "peça o texto da vaga"))
            self.assertIn("peça o texto", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
