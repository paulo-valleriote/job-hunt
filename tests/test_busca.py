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

    def test_limite_corta_pela_ordem_de_coleta_e_lista_as_cortadas(self):
        vs = [vaga(titulo=f"Vaga {i}", link=f"https://x/{i}") for i in range(1, 6)]
        ok, fora = b.processar(vs, "", maximo=3)
        self.assertEqual([v["titulo"] for v in ok], ["Vaga 1", "Vaga 2", "Vaga 3"])
        self.assertEqual([d["titulo"] for d in fora], ["Vaga 4", "Vaga 5"])
        self.assertIn("limite de 3", fora[0]["motivo"])

    def test_descartada_por_regra_nao_ocupa_lugar_no_limite(self):
        vs = [vaga(titulo="Velha", link="https://x/0", data="2026-10-20"),
              vaga(titulo="A", link="https://x/1"), vaga(titulo="B", link="https://x/2")]
        ok, fora = b.processar(vs, "", desde=DESDE, maximo=2)
        self.assertEqual([v["titulo"] for v in ok], ["A", "B"])
        self.assertEqual([d["titulo"] for d in fora], ["Velha"])

    def test_aceita_dentro_da_janela(self):
        self.assertEqual(len(b.processar([vaga()], "", desde=DESDE, hoje=HOJE)[0]), 1)


class Candidatos(unittest.TestCase):
    """selecionar(): da listagem de todas as URLs ao que será aberto e verificado."""

    def item(self, origem, n, **kw):
        return {"origem": origem, "id": f"{origem}{n:03d}".replace("A", "1").replace("B", "2").replace("C", "3"),
                "titulo": f"{origem}{n}", "empresa": f"Emp {origem}{n}", **kw}

    def ids(self, itens):
        return [i["titulo"] for i in itens]

    def test_rodizio_entre_urls_com_teto_por_url(self):
        itens = [self.item("A", n) for n in range(1, 9)] + [self.item("B", n) for n in range(1, 4)] \
              + [self.item("C", n) for n in range(1, 3)]
        sel = b.selecionar(itens, "", por_url=3, total=25)
        self.assertEqual(self.ids(sel), ["A1", "B1", "C1", "A2", "B2", "C2", "A3", "B3"])

    def test_mesmo_id_em_varias_urls_conta_uma_vez(self):
        repetida = self.item("A", 1)
        itens = [repetida, self.item("A", 2),
                 {**repetida, "origem": "B"}, self.item("B", 2), self.item("B", 3)]
        sel = b.selecionar(itens, "", por_url=2, total=25)
        self.assertEqual(self.ids(sel), ["A1", "B2", "A2", "B3"])

    def test_total_corta_o_rodizio(self):
        itens = [self.item(o, n) for o in "ABC" for n in range(1, 5)]
        self.assertEqual(self.ids(b.selecionar(itens, "", por_url=5, total=4)), ["A1", "B1", "C1", "A2"])

    def test_empresa_excluida_nao_ocupa_lugar(self):
        itens = [self.item("A", 1, empresa="Acme Corp"), self.item("A", 2), self.item("A", 3)]
        sel = b.selecionar(itens, EXC_OK, por_url=2, total=25)
        self.assertEqual(self.ids(sel), ["A2", "A3"])


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

    def test_mostra_a_evidencia_da_elegibilidade(self):
        v = vaga(elegibilidade="latam", evidencia="Remote - LATAM only")
        txt = b.render([v, vaga(titulo="Sem prova", link="https://x/7")], "2026-11-08", [], DESDE)
        self.assertIn("- Evidência: Remote - LATAM only", txt)
        self.assertIn("- Evidência: não registrada", txt)


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

    def grava(self, vagas, *args):
        self.res.write_text(json.dumps(vagas))
        out = self.p / "vagas"
        r = self.run_cli("gravar", "--resultados", str(self.res), "--saida-dir", str(out),
                         "--data", "2026-11-08", *args)
        return r, out

    def test_gravar_recusa_valor_invalido_de_enum(self):
        # Antes: "mundial" caía em "não confirma" sem ninguém ver o erro de digitação.
        for campo, valor in (("elegibilidade", "mundial"), ("modalidade", "remota"),
                             ("candidatura", "interna"), ("status", "fechada")):
            with self.subTest(campo=campo):
                r, out = self.grava([vaga(**{campo: valor})])
                self.assertEqual(r.returncode, 1, r.stdout)
                self.assertIn(campo, r.stderr)
                self.assertIn(valor, r.stderr)
                self.assertFalse(out.exists())

    def test_gravar_recusa_chave_desconhecida_ou_obrigatoria_ausente(self):
        com_typo = {**vaga(), "elegibilidad": "mundo"}
        r, out = self.grava([com_typo])
        self.assertEqual(r.returncode, 1)
        self.assertIn("elegibilidad", r.stderr)
        self.assertFalse(out.exists())
        sem_link = vaga()
        del sem_link["link"]
        r, out = self.grava([sem_link])
        self.assertEqual(r.returncode, 1)
        self.assertIn("link", r.stderr)

    def test_gravar_limita_a_20_por_padrao_e_aceita_max(self):
        vs = [vaga(titulo=f"Vaga {i}", link=f"https://x/{i}") for i in range(1, 23)]
        r, out = self.grava(vs)
        self.assertIn("20 vaga(s)", r.stdout)
        txt = (out / "2026-11-08-busca.md").read_text()
        self.assertIn("Vaga 22 | Beta SA | acima do limite de 20", txt)
        r, out = self.grava(vs, "--max", "5")
        self.assertIn("5 vaga(s)", r.stdout)

    def test_candidatos_imprime_json_da_selecao(self):
        itens = [{"origem": o, "id": f"{n}{i}", "titulo": f"{o}{i}", "empresa": f"E{o}{i}"}
                 for n, o in enumerate("ABC", 1) for i in range(1, 8)]
        lst = self.p / "lst.json"
        lst.write_text(json.dumps(itens))
        r = self.run_cli("candidatos", "--listagens", str(lst), "--por-url", "2", "--total", "5")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual([i["titulo"] for i in json.loads(r.stdout)], ["A1", "B1", "C1", "A2", "B2"])
        self.assertEqual(self.run_cli("candidatos", "--listagens", str(self.p / "nao_existe.json")).returncode, 2)


if __name__ == "__main__":
    unittest.main()
