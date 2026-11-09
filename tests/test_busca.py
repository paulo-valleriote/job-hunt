"""Testes do /busca (scripts/busca.py). Fixtures fictícias em diretório temporário.
Seams: janela_desde(), build_urls(), processar() (descartes), render() e a CLI (gate, arquivo)."""
import json, subprocess, sys, tempfile, unittest
from datetime import date
from urllib.parse import parse_qs, urlsplit
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts")); sys.path.insert(0, str(ROOT / "tests"))
import busca as b  # noqa: E402
from test_validar_config import BUSCA_OK, EXC_OK  # noqa: E402


def vaga(titulo="Dev Backend", empresa="Beta SA", link="https://www.linkedin.com/jobs/view/4487014884/", **kw):
    return {"titulo": titulo, "empresa": empresa, "link": link, "local": "Brasil (remoto)",
            "candidatura": "simplificada", "status": "aberta",
            "modalidade": "remoto", "elegibilidade": "brasil",
            "requisitos": "Vaga remota", "data": "2026-11-05", **kw}


HOJE, DESDE = date(2026, 11, 8), date(2026, 11, 1)
CFG = {"cargos_alvo": ["Engenheiro de Software Backend"], "regime": "remoto",
       "paises_fuso": ["Brasil", "EUA"], "faixa_salarial_minima": "9000",
       "stack_desejada": ["Python"], "deal_breakers": ["Plantão 24h"]}


class Urls(unittest.TestCase):
    def test_so_cargo_local_regime_e_janela(self):
        us = b.build_urls(CFG, DESDE, HOJE)
        self.assertEqual(len(us), 2)
        q = parse_qs(urlsplit(us[0]).query)
        self.assertEqual(q["keywords"], ["Engenheiro de Software Backend"])
        self.assertEqual(q["location"], ["Brazil"])
        self.assertEqual(q["f_WT"], ["2"])
        self.assertEqual(q["f_TPR"], [f"r{8 * 86400}"])
        self.assertEqual(parse_qs(urlsplit(us[1]).query)["location"], ["United States"])
        self.assertEqual(set(q) - {"keywords", "location", "geoId", "f_WT", "f_TPR", "sortBy"}, set())
        for u in us:
            for proibido in ("9000", "Python", "Plant"):
                self.assertNotIn(proibido, u)

    def test_geoid_do_pais_para_o_linkedin_nao_cair_na_localidade_da_conta(self):
        # O LinkedIn descarta "location=" e usa a localidade da conta; geoId fixa o país.
        us = b.build_urls({**CFG, "paises_fuso": ["Brasil", "EUA", "Reino Unido"]}, DESDE, HOJE)
        geo = [parse_qs(urlsplit(u).query)["geoId"] for u in us]
        self.assertEqual(geo, [["106057199"], ["103644278"], ["101165590"]])

    def test_america_latina_usa_o_geoid_da_regiao(self):
        # 91000011 = "América Latina" no LinkedIn (91000007 é Europa, Oriente Médio e África).
        for nome in ("América Latina", "LATAM"):
            q = parse_qs(urlsplit(b.build_urls({**CFG, "paises_fuso": [nome]}, DESDE, HOJE)[0]).query)
            self.assertEqual((q["location"], q["geoId"]), (["Latin America"], ["91000011"]))

    def test_pais_sem_geoid_conhecido_segue_so_com_location(self):
        q = parse_qs(urlsplit(b.build_urls({**CFG, "paises_fuso": ["Portugal"]}, DESDE, HOJE)[0]).query)
        self.assertEqual(q["location"], ["Portugal"])
        self.assertNotIn("geoId", q)

    def test_janela_desde_ultima_busca_anterior(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(b.janela_desde(d, HOJE), date(2026, 11, 1))
            for n in ("2026-11-03-busca.md", "2026-11-05-busca.md", "2026-11-08-busca.md"):
                (Path(d) / n).write_text("")
            self.assertEqual(b.janela_desde(d, HOJE), date(2026, 11, 5))

    def test_janela_tem_teto_de_30_dias(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "2026-01-01-busca.md").write_text("")
            self.assertEqual(b.janela_desde(d, HOJE), date(2026, 10, 9))


class Processar(unittest.TestCase):
    def motivos(self, vagas, exc="", **kw):
        return [d["motivo"] for d in b.processar(vagas, exc, **kw)[1]]

    def test_remove_duplicata_pelo_id_do_linkedin(self):
        a = vaga(link="https://br.linkedin.com/jobs/view/backend-at-beta-4487014884?trk=abc")
        c = vaga(titulo="Outro", empresa="Gama", link="https://www.linkedin.com/jobs/view/4487014884/")
        ok, fora = b.processar([a, c], "")
        self.assertEqual(len(ok), 1)
        self.assertEqual(fora[0]["motivo"], "duplicada")

    def test_remove_duplicata_por_titulo_e_empresa(self):
        a = vaga(link="https://x/1")
        c = vaga(titulo="  dev BACKEND ", empresa="beta sa", link="https://x/2")
        self.assertEqual(len(b.processar([a, c], "")[0]), 1)

    def test_mantem_distintas(self):
        a, c = vaga(), vaga(titulo="Dev Python", link="https://x/2")
        self.assertEqual(len(b.processar([a, c], "")[0]), 2)

    def test_exclui_empresa_de_vagas_excluidas(self):
        ok, fora = b.processar([vaga(empresa="Acme Corp", link="https://x/3"), vaga()], EXC_OK)
        self.assertEqual([v["empresa"] for v in ok], ["Beta SA"])
        self.assertIn("vagas_excluidas", fora[0]["motivo"])

    def test_comentarios_nao_excluem(self):
        self.assertEqual(len(b.processar([vaga(empresa="Beta SA")], "# Beta SA era exemplo\n")[0]), 1)

    def test_descarta_sem_data(self):
        self.assertIn("sem data", self.motivos([vaga(data="")])[0])

    def test_descarta_antes_da_janela(self):
        self.assertIn("antes de", self.motivos([vaga(data="2026-10-20")], desde=DESDE)[0])

    def test_descarta_data_futura(self):
        self.assertIn("inválida", self.motivos([vaga(data="2026-12-01")], hoje=HOJE)[0])

    def test_descarta_encerrada(self):
        self.assertIn("não aceita", self.motivos([vaga(status="encerrada")])[0])

    def test_remoto_descarta_hibrida_e_presencial(self):
        for m in ("híbrido", "Presencial"):
            self.assertIn("não é remota", self.motivos([vaga(modalidade=m)], remoto=True)[0])

    def test_remoto_descarta_modalidade_nao_verificada(self):
        self.assertIn("modalidade não verificada", self.motivos([vaga(modalidade="")], remoto=True)[0])

    def test_remoto_descarta_restrita_a_outro_pais(self):
        self.assertIn("outro país", self.motivos([vaga(elegibilidade="restrita")], remoto=True)[0])

    def test_remoto_descarta_elegibilidade_nao_confirmada(self):
        for e in ("", "nao_informada"):
            self.assertIn("não confirma", self.motivos([vaga(elegibilidade=e)], remoto=True)[0])

    def test_remoto_aceita_brasil_latam_e_mundo(self):
        vs = [vaga(elegibilidade=e, link=f"https://x/{e}", titulo=e) for e in ("brasil", "LATAM", "mundo")]
        self.assertEqual(len(b.processar(vs, "", remoto=True)[0]), 3)

    def test_sem_exigir_remoto_nao_checa_modalidade(self):
        self.assertEqual(len(b.processar([vaga(modalidade="híbrido", elegibilidade="")], "")[0]), 1)

    def test_aceita_dentro_da_janela(self):
        self.assertEqual(len(b.processar([vaga()], "", desde=DESDE, hoje=HOJE)[0]), 1)


class Render(unittest.TestCase):
    def test_grupos_com_numeracao_continua_e_descartadas(self):
        vs = [vaga(titulo="Ext A", candidatura="externa", link="https://x/1"),
              vaga(titulo="Simp B", link="https://x/2"),
              vaga(titulo="Ext C", candidatura="externa", link="https://x/3")]
        fora = [{"titulo": "Velha", "empresa": "Z", "link": "https://x/9", "motivo": "duplicada"}]
        txt = b.render(vs, "2026-11-08", fora, DESDE)
        self.assertLess(txt.index("Candidatura simplificada"), txt.index("Candidatura externa"))
        self.assertIn("## 1. Simp B", txt)
        self.assertIn("## 2. Ext A", txt)
        self.assertIn("## 3. Ext C", txt)
        self.assertIn("# Descartadas", txt)
        self.assertIn("Velha | Z | duplicada", txt)
        self.assertIn("desde 2026-11-01", txt)
        self.assertIn("- Modalidade: remoto (aceita candidatos de: brasil)", txt)


class Cli(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory()
        self.p = Path(self.d.name)
        self.exc = self.p / "exc.md"
        self.exc.write_text(EXC_OK)
        self.res = self.p / "res.json"
        self.res.write_text(json.dumps([vaga(), vaga(link="https://www.linkedin.com/jobs/view/4487014884?x=1"),
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
        r = self.run_cli("urls", busca=ex)
        self.assertEqual(r.returncode, 1)
        self.assertIn("exemplo", r.stderr.lower())
        out = self.p / "vagas"
        r = self.run_cli("gravar", "--resultados", str(self.res), "--saida-dir", str(out),
                         "--data", "2026-11-08", busca=ex)
        self.assertEqual(r.returncode, 1)
        self.assertFalse(out.exists())

    def test_recusa_excluidas_com_placeholder(self):
        self.exc.write_text("- 2026-10-01 | Empresa A | presencial | x\n")
        self.assertEqual(self.run_cli("urls").returncode, 1)

    def test_urls_imprime_desde_e_url(self):
        r = self.run_cli("urls", "--saida-dir", str(self.p / "vagas"), "--data", "2026-11-08")
        self.assertEqual(r.returncode, 0, r.stderr)
        linhas = r.stdout.splitlines()
        self.assertEqual(linhas[0], "desde 2026-11-01")
        self.assertTrue(linhas[1].startswith("https://www.linkedin.com/jobs/search/?"))
        self.assertNotIn("Python", r.stdout)

    def test_gravar_gera_arquivo_sem_classificar(self):
        out = self.p / "vagas"
        r = self.run_cli("gravar", "--resultados", str(self.res), "--saida-dir", str(out),
                         "--data", "2026-11-08")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("1 vaga(s)", r.stdout)
        txt = (out / "2026-11-08-busca.md").read_text()
        corpo = txt.split("# Descartadas")[0]
        for esperado in ("Dev Backend", "Beta SA", "https://www.linkedin.com/jobs/view/4487014884/",
                         "Vaga remota", "2026-11-05"):
            self.assertIn(esperado, corpo)
        self.assertNotIn("Acme", corpo)
        self.assertEqual(corpo.count("## "), 1)
        self.assertIn("Acme Corp", txt.split("# Descartadas")[1])
        for palavra in ("nota", "score", "aderência", "recomend"):
            self.assertNotIn(palavra, txt.lower())


if __name__ == "__main__":
    unittest.main()
