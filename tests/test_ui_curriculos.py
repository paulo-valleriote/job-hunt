"""Testes da lógica das telas Currículos e Tracker (ui/curriculos_core.py), sem Streamlit.
Seams: listar(), gerar() com runner injetado, ler_tracker(), salvar_tracker().
Só dados fictícios em diretório temporário; sem claude real, sem private/ real."""
import sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "ui"))
import curriculos_core as c  # noqa: E402
from scripts import enviei  # noqa: E402

RATING = "# Rating report\n\n| Versão | Nota |\n|---|---|\n| v1 | 7 |\n| v2 | 8.7 |\n\nEntregue: v2 (nota 8.7)\n"


def mk(base, nome, pdf=True, rating=True, cov=True):
    p = Path(base) / nome
    p.mkdir(parents=True)
    if pdf: (p / "curriculo.pdf").write_bytes(b"%PDF-fake")
    if rating: (p / "rating_report.md").write_text(RATING)
    if cov: (p / "coverage_review.md").write_text("## Lacunas\nNenhuma lacuna identificada.\n")
    return p


class Listar(unittest.TestCase):
    def test_vazio(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(c.listar(Path(d) / "nada"), [])

    def test_lista_mais_recente_primeiro_com_nota_e_arquivos(self):
        with tempfile.TemporaryDirectory() as d:
            mk(d, "2026-01-01-acme-dev"); mk(d, "2026-02-01-beta-qa", pdf=False, rating=False)
            r = c.listar(d)
            self.assertEqual([x["nome"] for x in r], ["2026-02-01-beta-qa", "2026-01-01-acme-dev"])
            self.assertIsNone(r[0]["nota"]); self.assertIsNone(r[0]["pdf"])
            self.assertEqual(r[1]["nota"], 8.7)
            self.assertTrue(r[1]["pdf"].name.endswith(".pdf"))
            self.assertIn("Lacunas", r[1]["coverage"])
            self.assertIn("Rating report", r[1]["rating"])


class Gerar(unittest.TestCase):
    def test_chama_claude_p_com_curriculo_e_devolve_pasta_nova(self):
        with tempfile.TemporaryDirectory() as d:
            chamadas = []
            def runner(cmd):
                chamadas.append(cmd); mk(d, "2026-03-01-x-y"); return 0, "ok"
            r = c.gerar("Vaga Python na Acme", d, runner)
            self.assertEqual(chamadas, [["claude", "-p", "/curriculo Vaga Python na Acme"]])
            self.assertEqual(r["nome"], "2026-03-01-x-y")

    def test_entrada_vazia(self):
        with self.assertRaises(ValueError):
            c.gerar("  ", "/tmp", lambda cmd: (0, ""))

    def test_falha_sem_pasta_nova(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(c.GeracaoFalhou):
                c.gerar("vaga", d, lambda cmd: (1, "boom"))


class Tracker(unittest.TestCase):
    def test_roundtrip_formato_excel_e_compativel_com_enviei(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "tracker.csv").write_bytes(("﻿" + ",".join(enviei.HEADER) + "\r\n").encode())
            enviei.main(["--private", d, "--empresa", "Acme", "--vaga", "Dev"])
            cab, linhas = c.ler_tracker(d)
            self.assertEqual(cab, enviei.HEADER)
            self.assertEqual(linhas[0]["empresa"], "Acme")
            linhas[0]["status"] = "entrevista"
            linhas.append({"empresa": "Beta, Inc", "vaga": "QA"})
            c.salvar_tracker(d, cab, linhas)
            raw = (Path(d) / "tracker.csv").read_bytes()
            self.assertTrue(raw.startswith(b"\xef\xbb\xbf")); self.assertIn(b"\r\n", raw)
            cab2, l2 = c.ler_tracker(d)
            self.assertEqual(l2[0]["status"], "entrevista")
            self.assertEqual(l2[1]["empresa"], "Beta, Inc")
            self.assertEqual(l2[1]["data"], "")

    def test_sem_tracker(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertIsNone(c.ler_tracker(d))
