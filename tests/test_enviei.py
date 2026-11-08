"""Testes do scripts/enviei.py. Só dados fictícios em diretório temporário."""
import csv, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "enviei.py"
HEADER = "data,empresa,vaga,fonte,tipo,link,curriculo,status,proximo_passo,observacoes"


def run(private, *args):
    return subprocess.run([sys.executable, str(SCRIPT), "--private", str(private), *args],
                          capture_output=True, text=True)


def rows(private):
    with open(Path(private) / "tracker.csv", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


class EnvieiTest(unittest.TestCase):
    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        self.p = Path(self._t.name)
        (self.p / "curriculos").mkdir()
        (self.p / "tracker.csv").write_text(HEADER + "\r\n", encoding="utf-8")

    def tearDown(self):
        self._t.cleanup()

    def test_adds_row_respecting_header(self):
        r = run(self.p, "--empresa", "Acme Ltda", "--vaga", "Dev Python",
                "--fonte", "LinkedIn", "--link", "http://x.test/1", "--data", "2026-01-05")
        self.assertEqual(r.returncode, 0, r.stderr)
        got = rows(self.p)
        self.assertEqual(len(got), 1)
        self.assertEqual(got[0]["empresa"], "Acme Ltda")
        self.assertEqual(got[0]["vaga"], "Dev Python")
        self.assertEqual(got[0]["data"], "2026-01-05")
        self.assertEqual(got[0]["status"], "enviada")
        self.assertEqual(got[0]["curriculo"], "")
        self.assertEqual((self.p / "tracker.csv").read_text(encoding="utf-8-sig").splitlines()[0], HEADER)

    def test_points_to_generated_resume(self):
        (self.p / "curriculos" / "2026-01-04-acme-ltda-dev-python").mkdir()
        (self.p / "curriculos" / "2026-01-04-outra-dev-python").mkdir()
        run(self.p, "--empresa", "Acme Ltda", "--vaga", "Dev Python")
        self.assertEqual(rows(self.p)[0]["curriculo"], "curriculos/2026-01-04-acme-ltda-dev-python")

    def test_no_duplicates(self):
        a = ["--empresa", "Acme Ltda", "--vaga", "Dev Python"]
        run(self.p, *a)
        r = run(self.p, "--empresa", "ACME ltda", "--vaga", "dev  python")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(len(rows(self.p)), 1)
        self.assertIn("já registrada", r.stdout)

    def test_excel_friendly_and_preserves_commas(self):
        run(self.p, "--empresa", "A, B", "--vaga", "Analista çã")
        raw = (self.p / "tracker.csv").read_bytes()
        self.assertTrue(raw.startswith(b"\xef\xbb\xbf"))
        self.assertNotIn(b"\r\r", raw)
        self.assertEqual(rows(self.p)[0]["empresa"], "A, B")
        self.assertEqual(rows(self.p)[0]["vaga"], "Analista çã")

    def test_missing_tracker_fails_without_creating(self):
        (self.p / "tracker.csv").unlink()
        r = run(self.p, "--empresa", "X", "--vaga", "Y")
        self.assertNotEqual(r.returncode, 0)
        self.assertFalse((self.p / "tracker.csv").exists())


if __name__ == "__main__":
    unittest.main()
