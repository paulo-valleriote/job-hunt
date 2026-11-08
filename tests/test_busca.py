"""Testes do /busca (scripts/busca.py). Fixtures fictícias em diretório temporário.
Seams: build_queries(), processar() (dedup + exclusões) e a CLI (gate, arquivo gerado)."""
import json, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts")); sys.path.insert(0, str(ROOT / "tests"))
import busca as b  # noqa: E402
from test_validar_config import BUSCA_OK, EXC_OK  # noqa: E402


def vaga(titulo="Dev Backend", empresa="Beta SA", link="https://www.linkedin.com/jobs/view/111", **kw):
    return {"titulo": titulo, "empresa": empresa, "link": link,
            "trecho": "Vaga remota", "data": "2026-11-01", **kw}


class Queries(unittest.TestCase):
    def test_so_cargo_local_regime(self):
        qs = b.build_queries({"cargos_alvo": ["Engenheiro de Software Backend"], "regime": "remoto",
                              "paises_fuso": ["Brasil"], "faixa_salarial_minima": "9000",
                              "stack_desejada": ["Python"], "deal_breakers": ["Plantão 24h"]})
        self.assertEqual(qs, ['Engenheiro de Software Backend remoto Brasil site:linkedin.com/jobs'])
        for q in qs:
            for proibido in ("9000", "Python", "Plantão"):
                self.assertNotIn(proibido, q)


class Processar(unittest.TestCase):
    def test_remove_duplicata_por_link_ignorando_query_string(self):
        a = vaga(link="https://www.linkedin.com/jobs/view/111?trk=abc")
        c = vaga(titulo="Outro", empresa="Gama", link="https://www.linkedin.com/jobs/view/111/")
        self.assertEqual(len(b.processar([a, c], "")), 1)

    def test_remove_duplicata_por_titulo_e_empresa(self):
        a = vaga(link="https://x/1")
        c = vaga(titulo="  dev BACKEND ", empresa="beta sa", link="https://x/2")
        self.assertEqual(len(b.processar([a, c], "")), 1)

    def test_mantem_distintas(self):
        a, c = vaga(), vaga(titulo="Dev Python", link="https://x/2")
        self.assertEqual(len(b.processar([a, c], "")), 2)

    def test_exclui_empresa_de_vagas_excluidas(self):
        r = b.processar([vaga(empresa="Acme Corp", link="https://x/3"), vaga()], EXC_OK)
        self.assertEqual([v["empresa"] for v in r], ["Beta SA"])

    def test_comentarios_nao_excluem(self):
        r = b.processar([vaga(empresa="Beta SA")], "# Beta SA era exemplo\n")
        self.assertEqual(len(r), 1)


class Cli(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory()
        self.p = Path(self.d.name)
        self.exc = self.p / "exc.md"
        self.exc.write_text(EXC_OK)
        self.res = self.p / "res.json"
        self.res.write_text(json.dumps([vaga(), vaga(link="https://www.linkedin.com/jobs/view/111?x=1"),
                                        vaga(empresa="Acme Corp", link="https://x/9")]))

    def tearDown(self):
        self.d.cleanup()

    def run_cli(self, *args, busca=BUSCA_OK):
        bf = self.p / "busca.yaml"
        bf.write_text(busca)
        return subprocess.run([sys.executable, str(ROOT / "scripts/busca.py"), *args,
                               "--busca", str(bf), "--excluidas", str(self.exc)],
                              capture_output=True, text=True)

    def test_recusa_com_placeholder(self):
        ex = (ROOT / "busca.example.yaml").read_text()
        r = self.run_cli("queries", busca=ex)
        self.assertEqual(r.returncode, 1)
        self.assertIn("exemplo", r.stderr.lower())
        out = self.p / "vagas"
        r = self.run_cli("gravar", "--resultados", str(self.res), "--saida-dir", str(out),
                         "--data", "2026-11-08", busca=ex)
        self.assertEqual(r.returncode, 1)
        self.assertFalse(out.exists())

    def test_recusa_excluidas_com_placeholder(self):
        self.exc.write_text("- 2026-10-01 | Empresa A | presencial | x\n")
        self.assertEqual(self.run_cli("queries").returncode, 1)

    def test_queries_imprime_consulta(self):
        r = self.run_cli("queries")
        self.assertEqual(r.returncode, 0)
        self.assertIn("Engenheiro de Software Backend remoto Brasil", r.stdout)
        self.assertNotIn("Python", r.stdout)

    def test_gravar_gera_arquivo_sem_classificar(self):
        out = self.p / "vagas"
        r = self.run_cli("gravar", "--resultados", str(self.res), "--saida-dir", str(out),
                         "--data", "2026-11-08")
        self.assertEqual(r.returncode, 0, r.stderr)
        txt = (out / "2026-11-08-busca.md").read_text()
        self.assertIn("Dev Backend", txt)
        self.assertIn("Beta SA", txt)
        self.assertIn("https://www.linkedin.com/jobs/view/111", txt)
        self.assertIn("Vaga remota", txt)
        self.assertIn("2026-11-01", txt)
        self.assertNotIn("Acme", txt)
        self.assertEqual(txt.count("Dev Backend"), 1)
        for palavra in ("nota", "score", "aderência", "recomend"):
            self.assertNotIn(palavra, txt.lower())


if __name__ == "__main__":
    unittest.main()
