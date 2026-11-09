"""Testes do /curriculo básico (scripts/curriculo.py).
Seams: detectar_idioma(), pasta_saida(), validar_coverage(), gerar_pdf() (upstream e pdflatex
falsos, injetados via vendor= e PATH) e a CLI. Só dados fictícios em diretório temporário."""
import os, stat, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import curriculo as c  # noqa: E402

COV_OK = "# Coverage\n## Cobertura\n- Python: ok\n## Lacunas\n- Kubernetes: não consta no perfil.\n"


def exe(path, body):
    Path(path).write_text("#!/bin/sh\n" + body)
    Path(path).chmod(Path(path).stat().st_mode | stat.S_IEXEC)


def fake_vendor(d, valida_rc=0):
    s = Path(d) / "vendor/meu-emprego-novo/meu-emprego-novo-pipeline/scripts"
    s.mkdir(parents=True)
    (s / "validar_json.py").write_text(f"import sys; sys.exit({valida_rc})\n")
    (s / "json_para_latex.py").write_text(
        "import sys; open(sys.argv[2],'w').write('\\\\documentclass{article}')\n")
    return Path(d) / "vendor/meu-emprego-novo"


def fake_pdflatex(d, rc=0):
    b = Path(d) / "bin"; b.mkdir()
    exe(b / "pdflatex", 'for a; do last=$a; done\n'
        f'[ {rc} -eq 0 ] && : > "$(dirname "$last")/curriculo.pdf" ; exit {rc}\n')
    return b


class Idioma(unittest.TestCase):
    def test_en(self):
        self.assertEqual(c.detectar_idioma("We are looking for a developer with experience in the team and you will work with us"), "en")

    def test_pt(self):
        self.assertEqual(c.detectar_idioma("Buscamos pessoa desenvolvedora com experiência em Python para atuar no nosso time e com a equipe"), "pt")

    def test_forcado_vence(self):
        self.assertEqual(c.detectar_idioma("Buscamos pessoa com experiência para o time", forcar="en"), "en")

    def test_forcado_invalido(self):
        with self.assertRaises(ValueError):
            c.detectar_idioma("x", forcar="fr")

    def test_empate_cai_em_en(self):
        self.assertEqual(c.detectar_idioma("Python Django"), "en")


class Pasta(unittest.TestCase):
    def test_cria_pasta(self):
        with tempfile.TemporaryDirectory() as d:
            p = c.pasta_saida(d, "2026-01-05", "Acme Corp", "Dev Backend Sênior")
            self.assertTrue(p.is_dir())
            self.assertEqual(p.name, "2026-01-05-acme-corp-dev-backend-senior")


class Coverage(unittest.TestCase):
    def test_ok(self):
        self.assertEqual(c.validar_coverage(COV_OK), [])

    def test_sem_lacunas(self):
        self.assertTrue(c.validar_coverage("# x\n## Cobertura\n- a\n"))


class Gerar(unittest.TestCase):
    def rodar(self, d, valida_rc=0, tex_rc=0, json_ok=True):
        out = Path(d) / "out"; out.mkdir()
        if json_ok:
            (out / "resume.json").write_text("{}")
        v = fake_vendor(d, valida_rc)
        b = fake_pdflatex(d, tex_rc)
        old = os.environ["PATH"]; os.environ["PATH"] = f"{b}:{old}"
        try:
            return out, c.gerar_pdf(out, vendor=v)
        finally:
            os.environ["PATH"] = old

    def test_fluxo_completo(self):
        with tempfile.TemporaryDirectory() as d:
            out, erros = self.rodar(d)
            self.assertEqual(erros, [])
            self.assertTrue((out / "curriculo.tex").is_file())
            self.assertTrue((out / "curriculo.pdf").is_file())

    def test_validador_falha_nao_gera(self):
        with tempfile.TemporaryDirectory() as d:
            out, erros = self.rodar(d, valida_rc=1)
            self.assertTrue(erros)
            self.assertFalse((out / "curriculo.tex").exists())

    def test_pdflatex_falha(self):
        with tempfile.TemporaryDirectory() as d:
            out, erros = self.rodar(d, tex_rc=1)
            self.assertTrue(erros)

    def test_sem_json(self):
        with tempfile.TemporaryDirectory() as d:
            out, erros = self.rodar(d, json_ok=False)
            self.assertTrue(erros)

    def test_sem_vendor(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "resume.json").write_text("{}")
            self.assertIn("make setup", " ".join(c.gerar_pdf(d, vendor=Path(d) / "nada")))


def resume_fake(summary, highlights):
    return {"basics": {"name": "Fulana", "label": "Dev", "email": "f@example.com", "summary": summary},
            "work": [{"name": "Empresa Fictícia", "position": "Dev", "startDate": "2020",
                      "highlights": highlights}],
            "education": [], "skills": []}


class Lint(unittest.TestCase):
    RESUMO_PT = "Desenvolvedora com experiência em Python para times de produto e com foco em APIs."

    def test_destaque_em_ingles_em_curriculo_pt_gera_um_aviso(self):
        avisos = c.lint_resume(resume_fake(self.RESUMO_PT,
                                           ["Desenvolvi APIs em Python para o time de produto",
                                            "Led the team to deliver features with our partners"]), "pt")
        self.assertEqual(len(avisos), 1)
        self.assertIn("destaque 2", avisos[0])

    def test_curriculo_coerente_sem_avisos(self):
        self.assertEqual(c.lint_resume(resume_fake(self.RESUMO_PT,
                                                   ["Desenvolvi APIs em Python para o time de produto"]), "pt"), [])

    def test_campo_so_com_siglas_sem_aviso(self):
        self.assertEqual(c.lint_resume(resume_fake("AWS, API, SQL e CI/CD", ["ETL com AWS e SQL"]), "pt"), [])

    def test_resumo_em_ingles_com_idioma_pt_avisa(self):
        avisos = c.lint_resume(resume_fake("Engineer with experience in the cloud and data for the team",
                                           ["Desenvolvi APIs em Python"]), "pt")
        self.assertEqual(len(avisos), 1)
        self.assertIn("summary", avisos[0])

    def test_voz_3a_pessoa_em_pt_avisa(self):
        avisos = c.lint_resume(resume_fake(self.RESUMO_PT, ["Desenvolveu APIs em Python"]), "pt")
        self.assertEqual(len(avisos), 1)
        self.assertIn("3ª pessoa", avisos[0])

    def test_voz_1a_pessoa_em_pt_passa(self):
        self.assertEqual(c.lint_resume(resume_fake(self.RESUMO_PT, ["Criei pipelines de dados"]), "pt"), [])

    def test_voz_en(self):
        self.assertEqual(c.lint_resume(resume_fake("Engineer with experience in cloud for the team",
                                                   ["Developed APIs in Python"]), "en"), [])
        avisos = c.lint_resume(resume_fake("Engineer with experience in cloud for the team",
                                           ["Leads a team of engineers"]), "en")
        self.assertEqual(len(avisos), 1)
        self.assertIn("3ª pessoa", avisos[0])

    def test_lint_pasta_sempre_sai_zero(self):
        with tempfile.TemporaryDirectory() as d:
            import json as _j
            (Path(d) / "resume.json").write_text(_j.dumps(
                resume_fake(self.RESUMO_PT, ["Desenvolveu APIs"]), ensure_ascii=False), encoding="utf-8")
            self.assertEqual(c.lint(d, "pt"), c.lint_resume(_j.loads((Path(d) / "resume.json").read_text(encoding="utf-8")), "pt"))


class CLI(unittest.TestCase):
    def run_cli(self, *a):
        return subprocess.run([sys.executable, str(ROOT / "scripts/curriculo.py"), *a],
                              capture_output=True, text=True)

    def test_idioma(self):
        r = self.run_cli("idioma", "Buscamos pessoa com experiência para o time", "--forcar", "en")
        self.assertEqual(r.stdout.strip(), "en")

    def test_pasta(self):
        with tempfile.TemporaryDirectory() as d:
            r = self.run_cli("pasta", "--base", d, "--empresa", "Acme", "--cargo", "Dev", "--data", "2026-01-05")
            self.assertEqual(r.returncode, 0)
            self.assertTrue(Path(r.stdout.strip()).is_dir())

    def test_lint_cli_avisa_e_sai_zero(self):
        import json as _j
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "resume.json").write_text(_j.dumps(
                resume_fake("Desenvolvedora com experiência em Python para o time", ["Led the team to deliver features"])), encoding="utf-8")
            r = self.run_cli("lint", d, "--idioma", "pt")
            self.assertEqual(r.returncode, 0)
            self.assertIn("destaque 1", r.stdout)
            r2 = self.run_cli("lint", d + "/inexistente", "--idioma", "pt")
            self.assertEqual(r2.returncode, 0)
            self.assertIn("resume.json", r2.stdout)

    def test_coverage_invalido(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "c.md"; f.write_text("# vazio\n")
            self.assertNotEqual(self.run_cli("coverage", str(f)).returncode, 0)


if __name__ == "__main__":
    unittest.main()
