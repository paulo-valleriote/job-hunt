"""Testes do /busca (scripts/busca.py). Fixtures fictícias em diretório temporário.
Seams: janela_desde(), build_urls(), processar() (descartes), render() e a CLI (gate, arquivo)."""
import json, subprocess, sys, tempfile, unittest, urllib.error
from datetime import date
from urllib.parse import parse_qs, urlsplit
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts")); sys.path.insert(0, str(ROOT / "tests"))
import busca as b  # noqa: E402
import fontes as f  # noqa: E402
import coleta as co  # noqa: E402
import himalayas as hm  # noqa: E402
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
        self.assertIn("duplicada", fora[0]["motivo"])

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

    def test_titulo_com_termo_excluido_vai_para_descartadas_com_motivo(self):
        vs = [vaga("Staff Engineer", link="https://x/1"), vaga("PRINCIPAL Software Engineer", link="https://x/2"),
              vaga("Engenheiro Líder Técnico", link="https://x/3"), vaga("Dev Backend", link="https://x/4")]
        ok, fora = b.processar(vs, "", titulos_excluidos=["Staff", "Principal", "líder"])
        self.assertEqual([v["titulo"] for v in ok], ["Dev Backend"])
        self.assertEqual(len(fora), 3)
        self.assertTrue(all("nível acima" in d["motivo"] for d in fora), fora)
        self.assertIn("'Staff'", fora[0]["motivo"])

    def test_termo_ignora_acento_e_caixa_e_exige_palavra_inteira(self):
        vs = [vaga("Head de Engenharia", link="https://x/1"), vaga("Lider Tecnico", link="https://x/2"),
              vaga("Leadership Coach Dev", link="https://x/3"), vaga("Overhead Dev", link="https://x/4")]
        ok, fora = b.processar(vs, "", titulos_excluidos=["head", "Líder Técnico", "Lead"])
        self.assertEqual([v["titulo"] for v in ok], ["Leadership Coach Dev", "Overhead Dev"])
        self.assertEqual(len(fora), 2)

    def test_senior_sem_termo_da_lista_continua_aceita(self):
        vs = [vaga("Senior Backend Engineer", link="https://x/1"), vaga("Sr. Python Developer", link="https://x/2")]
        ok, fora = b.processar(vs, "", titulos_excluidos=["Staff", "Principal", "Lead", "Head", "Director"])
        self.assertEqual(len(ok), 2)
        self.assertEqual(fora, [])

    def test_senior_com_termo_da_lista_e_descartada(self):
        ok, fora = b.processar([vaga("Senior Staff Engineer")], "", titulos_excluidos=["Staff"])
        self.assertEqual(ok, [])
        self.assertEqual(len(fora), 1)

    def test_campo_ausente_ou_vazio_nao_muda_o_comportamento(self):
        vs = [vaga("Staff Engineer", link="https://x/1"), vaga("Principal Engineer", link="https://x/2")]
        for kw in ({}, {"titulos_excluidos": []}, {"titulos_excluidos": None}, {"titulos_excluidos": [""]}):
            self.assertEqual(len(b.processar(vs, "", **kw)[0]), 2, kw)

    def test_aceita_dentro_da_janela(self):
        self.assertEqual(len(b.processar([vaga()], "", desde=DESDE, hoje=HOJE)[0]), 1)


class DedupeEntreFontes(unittest.TestCase):
    """Ticket 05: mesma vaga em duas fontes aparece uma vez, com o link do ATS; rodízio sob o teto."""
    LI = "https://www.linkedin.com/jobs/view/4487014884/"
    ATS = "https://boards.greenhouse.io/beta/jobs/555"

    def test_ats_vence_linkedin_quando_o_linkedin_vem_primeiro(self):
        li = vaga(link=self.LI, fonte="linkedin")
        ats = vaga(link=self.ATS, fonte="greenhouse:beta", candidatura="externa")
        ok, fora = b.processar([li, ats], "")
        self.assertEqual([v["link"] for v in ok], [self.ATS])
        self.assertEqual(ok[0]["fontes_secundarias"], ["linkedin"])
        self.assertIn("duplicada", fora[0]["motivo"])
        self.assertEqual(fora[0]["link"], self.LI)

    def test_ats_vence_linkedin_quando_o_ats_vem_primeiro(self):
        ats = vaga(link=self.ATS, fonte="greenhouse:beta", candidatura="externa")
        li = vaga(link=self.LI, fonte="linkedin")
        ok, fora = b.processar([ats, li], "")
        self.assertEqual([v["link"] for v in ok], [self.ATS])
        self.assertEqual(ok[0]["fontes_secundarias"], ["linkedin"])
        self.assertEqual(len(fora), 1)

    def test_linkedin_sem_campo_fonte_conta_como_linkedin(self):
        li = vaga(link=self.LI)  # vaga antiga, sem "fonte"
        ats = vaga(link=self.ATS, fonte="lever:neon", candidatura="externa")
        ok, _ = b.processar([li, ats], "")
        self.assertEqual([v["link"] for v in ok], [self.ATS])
        self.assertEqual(ok[0]["fontes_secundarias"], ["linkedin"])

    def test_duplicata_entre_agregadores_mantem_a_primeira_e_registra_a_outra(self):
        li = vaga(link=self.LI)
        him = vaga(link="https://himalayas.app/jobs/beta-dev", fonte="himalayas")
        ok, fora = b.processar([li, him], "")
        self.assertEqual([v["link"] for v in ok], [self.LI])
        self.assertEqual(ok[0]["fontes_secundarias"], ["himalayas"])
        self.assertEqual(len(fora), 1)

    def test_mesmo_link_com_query_diferente_e_duplicata(self):
        a = vaga(titulo="Dev A", link="https://boards.greenhouse.io/beta/jobs/555?gh_src=x", fonte="greenhouse:beta")
        c = vaga(titulo="Dev B", link="https://boards.greenhouse.io/beta/jobs/555?utm=1", fonte="greenhouse:beta")
        self.assertEqual(len(b.processar([a, c], "")[0]), 1)

    def test_rodizio_divide_o_teto_entre_fontes(self):
        li = [vaga(titulo=f"LI {i}", link=f"https://www.linkedin.com/jobs/view/{100000 + i}/", fonte="linkedin")
              for i in range(5)]
        gh = [vaga(titulo=f"GH {i}", empresa=f"Emp {i}", link=f"https://boards.greenhouse.io/e/jobs/{i}",
                   fonte="greenhouse:e", candidatura="externa") for i in range(5)]
        ok, fora = b.processar(li + gh, "", maximo=4)
        self.assertEqual([v["titulo"] for v in ok], ["LI 0", "LI 1", "GH 0", "GH 1"])
        self.assertEqual(len(fora), 6)
        self.assertTrue(all("rodízio" in d["motivo"] for d in fora[-6:]))

    def test_fonte_com_pouca_vaga_repassa_a_sobra_a_outra(self):
        li = [vaga(titulo=f"LI {i}", link=f"https://www.linkedin.com/jobs/view/{100000 + i}/") for i in range(5)]
        gh = [vaga(titulo="GH 0", empresa="Emp 0", link="https://boards.greenhouse.io/e/jobs/0",
                   fonte="greenhouse:e", candidatura="externa")]
        ok, _ = b.processar(li + gh, "", maximo=4)
        self.assertEqual(sorted(v["titulo"] for v in ok), ["GH 0", "LI 0", "LI 1", "LI 2"])

    def test_rodizio_nao_muda_a_ordem_quando_ha_so_uma_fonte(self):
        vs = [vaga(titulo=f"Vaga {i}", link=f"https://x/{i}") for i in range(1, 5)]
        ok, _ = b.processar(vs, "", maximo=2)
        self.assertEqual([v["titulo"] for v in ok], ["Vaga 1", "Vaga 2"])

    def test_render_mostra_fontes_secundarias(self):
        ats = vaga(link=self.ATS, fonte="greenhouse:beta", candidatura="externa")
        li = vaga(link=self.LI, fonte="linkedin")
        ok, fora = b.processar([li, ats], "")
        txt = b.render(ok, "2026-11-08", fora, DESDE)
        self.assertIn("Também encontrada em: linkedin", txt)


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


class TitulosExcluidos(unittest.TestCase):
    """O campo titulos_excluidos do busca.yaml, lido pelos comandos candidatos e gravar."""

    def test_parse_aceita_lista_valor_unico_e_ausente(self):
        self.assertEqual(b.titulos_excluidos(b.parse_busca("titulos_excluidos:\n  - Staff\n  - Lead\n")),
                         ["Staff", "Lead"])
        self.assertEqual(b.titulos_excluidos(b.parse_busca("titulos_excluidos: Staff\n")), ["Staff"])
        self.assertEqual(b.titulos_excluidos(b.parse_busca("titulos_excluidos:\nregime: remoto\n")), [])
        self.assertEqual(b.titulos_excluidos(b.parse_busca("regime: remoto\n")), [])


class Filtros(unittest.TestCase):
    """filtros_extras(): o que o LinkedIn aplicou além do que pedimos."""

    FINAL = ("https://www.linkedin.com/jobs/search-results/?currentJobId=4444445689&keywords=Backend%20Developer"
             "&geoId=106057199&f_TPR=r172800&f_SAL=f_SA_id_225001%3A272001")

    def test_aponta_filtro_que_nao_pedimos(self):
        self.assertEqual(b.filtros_extras(self.FINAL), {"f_SAL": "f_SA_id_225001:272001"})

    def test_url_so_com_o_pedido_nao_tem_extra(self):
        ok = "https://www.linkedin.com/jobs/search-results/?currentJobId=1&keywords=Go&geoId=1&f_TPR=r1&f_WT=2&sortBy=DD"
        self.assertEqual(b.filtros_extras(ok), {})


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

    def test_gravar_limita_a_50_por_padrao_e_aceita_max(self):
        vs = [vaga(titulo=f"Vaga {i}", link=f"https://x/{i}") for i in range(1, 53)]
        r, out = self.grava(vs)
        self.assertIn("50 vaga(s)", r.stdout)
        txt = (out / "2026-11-08-busca.md").read_text()
        self.assertIn("Vaga 52 | Beta SA | acima do limite de 50", txt)
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

    def test_candidatos_descarta_por_titulo_antes_da_verificacao(self):
        itens = [{"origem": "A", "id": str(n), "titulo": t, "empresa": f"E{n}"}
                 for n, t in enumerate(["Staff Engineer", "Senior Backend Engineer", "Dev Pleno", "Head of Eng"], 1)]
        lst = self.p / "lst.json"
        lst.write_text(json.dumps(itens))
        busca = BUSCA_OK + "titulos_excluidos:\n  - Staff\n  - Head\n"
        r = self.run_cli("candidatos", "--listagens", str(lst), busca=busca)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual([i["titulo"] for i in json.loads(r.stdout)], ["Senior Backend Engineer", "Dev Pleno"])
        self.assertIn("Staff Engineer", r.stderr)
        r = self.run_cli("candidatos", "--listagens", str(lst))  # sem o campo: nada muda
        self.assertEqual(len(json.loads(r.stdout)), 4)

    def test_gravar_lista_a_vaga_de_nivel_acima_em_descartadas(self):
        self.res.write_text(json.dumps([vaga("Staff Engineer", link="https://x/1"),
                                        vaga("Senior Engineer", link="https://x/2")]))
        busca = BUSCA_OK + "titulos_excluidos:\n  - Staff\n"
        r = self.run_cli("gravar", "--resultados", str(self.res), "--saida-dir", str(self.p / "out"),
                         "--data", "2026-11-08", "--desde", "2026-11-01", busca=busca)
        self.assertEqual(r.returncode, 0, r.stderr)
        txt = (self.p / "out/2026-11-08-busca.md").read_text()
        self.assertIn("## 1. Senior Engineer", txt)
        self.assertIn("- Staff Engineer | Beta SA | nível acima do alvo", txt)

    def test_filtros_imprime_extras_ou_diz_que_nao_ha(self):
        r = self.run_cli("filtros", "--url", Filtros.FINAL)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("f_SAL=f_SA_id_225001:272001", r.stdout)
        r = self.run_cli("filtros", "--url", "https://www.linkedin.com/jobs/search-results/?keywords=Go&f_TPR=r1")
        self.assertIn("nenhum filtro extra", r.stdout)
        self.assertEqual(self.run_cli("filtros").returncode, 2)


class FontesAts(unittest.TestCase):
    """Lista versionada de tokens de ATS (scripts/fontes.py): só entra token com evidência."""
    ENTRADA = {"empresa": "Acme", "ats": "greenhouse", "token": "acme",
               "evidencia_url": "https://boards-api.greenhouse.io/v1/boards/acme/jobs",
               "verificado_em": "2026-11-11", "vinculo": "conteudo_das_vagas"}

    def test_lista_inicial_traz_os_dez_tokens_com_evidencia_e_vinculo(self):
        entradas = f.carregar_fontes(ROOT / "fontes_ats.json")
        tokens = {(e["ats"], e["token"]) for e in entradas}
        self.assertEqual(tokens, {("greenhouse", t) for t in ("ebanx", "quintoandar", "stone", "gympass",
                                                              "vtex", "inter", "c6bank", "rdstation")}
                                 | {("ashby", "nubank"), ("lever", "neon")})
        oficiais = {e["token"] for e in entradas if e["vinculo"] == "pagina_oficial"}
        self.assertEqual(oficiais, {"ebanx", "neon"})
        for e in entradas:
            with self.subTest(token=e["token"]):
                self.assertEqual(e["verificado_em"], "2026-11-11")
                self.assertTrue(e["evidencia_url"].startswith("https://"))

    def test_entrada_sem_evidencia_e_recusada(self):
        sem = {k: v for k, v in self.ENTRADA.items() if k != "evidencia_url"}
        self.assertTrue(any("evidencia_url" in p for p in f.validar_fontes([sem])))
        vazia = {**self.ENTRADA, "evidencia_url": "  "}
        self.assertTrue(f.validar_fontes([vazia]))
        with tempfile.TemporaryDirectory() as d:
            arq = Path(d) / "fontes.json"
            arq.write_text(json.dumps([sem]))
            with self.assertRaises(ValueError):
                f.carregar_fontes(arq)

    def test_recusa_ats_vinculo_e_data_invalidos_e_chave_desconhecida(self):
        for campo, valor in (("ats", "gupy"), ("vinculo", "talvez"), ("verificado_em", "11/11/2026")):
            with self.subTest(campo=campo):
                self.assertTrue(f.validar_fontes([{**self.ENTRADA, campo: valor}]))
        self.assertTrue(f.validar_fontes([{**self.ENTRADA, "tokn": "x"}]))
        self.assertEqual(f.validar_fontes([self.ENTRADA]), [])

    def test_gravar_aceita_fonte_e_atribuicao_e_segue_recusando_chave_desconhecida(self):
        ok = vaga(fonte="Himalayas", atribuicao="Fonte: Himalayas")
        self.assertEqual(b.validar_vagas([ok]), [])
        self.assertTrue(b.validar_vagas([vaga(fonte_typo="x")]))

    def test_render_mostra_fonte_e_atribuicao_quando_houver(self):
        txt = b.render([vaga(fonte="Greenhouse: stone", atribuicao="", link="https://x/1"),
                        vaga(titulo="Hima", fonte="Himalayas", atribuicao="Fonte: Himalayas",
                             link="https://x/2"),
                        vaga(titulo="Sem fonte", link="https://x/3")], "2026-11-08", [], DESDE)
        self.assertIn("- Fonte: Greenhouse: stone", txt)
        self.assertIn("- Atribuição: Fonte: Himalayas", txt)
        self.assertIn("- Fonte: não registrada", txt)
        self.assertEqual(txt.count("- Atribuição:"), 1)


GH_URL = "https://boards-api.greenhouse.io/v1/boards/{}/jobs"


def _gh_job(i, titulo, local, publicada="2026-11-05T10:00:00-03:00"):
    return {"id": i, "title": titulo, "absolute_url": f"https://job-boards.greenhouse.io/acme/jobs/{i}",
            "location": {"name": local}, "first_published": publicada,
            "updated_at": "2026-11-06T10:00:00-03:00", "requisition_id": "R-1", "internal_job_id": 9,
            "company_name": "Acme", "content": "DESCRIÇÃO COMPLETA QUE NÃO PODE SER GRAVADA"}


# Resposta gravada (fictícia) do endpoint público de lista de vagas do Greenhouse.
GH_OK = json.dumps({"jobs": [_gh_job(1, "Engenheiro Backend", "São Paulo, São Paulo, Brasil"),
                             _gh_job(2, "Backend Engineer", "Remote"),
                             _gh_job(3, "Staff Engineer", "Remote - Brazil")], "meta": {"total": 3}})
ACME = {"empresa": "Acme", "ats": "greenhouse", "token": "acme", "evidencia_url": GH_URL.format("acme"),
        "verificado_em": "2026-11-11", "vinculo": "conteudo_das_vagas"}


class Fake:
    """Fetcher injetável: respostas gravadas por URL; levanta a exceção quando o valor é uma."""
    def __init__(self, respostas):
        self.respostas, self.chamadas = respostas, []

    def __call__(self, url):
        self.chamadas.append(url)
        r = self.respostas[url]
        if isinstance(r, Exception):
            raise r
        return r


def _fonte(token, **kw):
    return {**ACME, "empresa": token.title(), "token": token, "evidencia_url": GH_URL.format(token), **kw}


class ColetaGreenhouse(unittest.TestCase):
    def coletar(self, fontes, fake):
        return co.coletar(fontes, fake, pausa=(0, 0), sleep=lambda s: None)

    def test_sucesso_mapeia_para_o_formato_comum(self):
        vagas, falhas = self.coletar([ACME], Fake({GH_URL.format("acme"): GH_OK}))
        self.assertEqual(falhas, [])
        self.assertEqual([v["titulo"] for v in vagas], ["Engenheiro Backend", "Backend Engineer", "Staff Engineer"])
        v = vagas[0]
        self.assertEqual((v["empresa"], v["link"], v["local"], v["data"]),
                         ("Acme", "https://job-boards.greenhouse.io/acme/jobs/1",
                          "São Paulo, São Paulo, Brasil", "2026-11-05"))
        self.assertEqual((v["fonte"], v["candidatura"], v["status"]), ("greenhouse:acme", "externa", "aberta"))
        self.assertEqual((v["elegibilidade"], v["modalidade"]), ("brasil", ""))
        self.assertEqual(vagas[1]["elegibilidade"], "nao_informada")
        self.assertEqual(vagas[1]["modalidade"], "remoto")
        self.assertEqual(b.validar_vagas(vagas), [])

    def test_nao_grava_descricao_completa(self):
        vagas, _ = self.coletar([ACME], Fake({GH_URL.format("acme"): GH_OK}))
        for v in vagas:
            with self.subTest(titulo=v["titulo"]):
                self.assertNotIn("content", v)
                self.assertFalse(v.get("requisitos"))
                self.assertNotIn("DESCRIÇÃO", json.dumps(v, ensure_ascii=False))

    def test_pede_so_o_token_publico_sem_conteudo(self):
        fake = Fake({GH_URL.format("acme"): GH_OK})
        self.coletar([ACME], fake)
        self.assertEqual(fake.chamadas, [GH_URL.format("acme")])

    def test_404_timeout_5xx_e_json_invalido_viram_falha_e_a_rodada_segue(self):
        fontes = [_fonte(t) for t in "abcde"]
        fake = Fake({
            GH_URL.format("a"): urllib.error.HTTPError(GH_URL.format("a"), 404, "Not Found", None, None),
            GH_URL.format("b"): TimeoutError("timed out"),
            GH_URL.format("c"): urllib.error.HTTPError(GH_URL.format("c"), 503, "Unavailable", None, None),
            GH_URL.format("d"): "<html>não é JSON</html>",
            GH_URL.format("e"): GH_OK,
        })
        vagas, falhas = self.coletar(fontes, fake)
        self.assertEqual(len(fake.chamadas), 5)
        self.assertEqual(len(vagas), 3)
        self.assertEqual({v["fonte"] for v in vagas}, {"greenhouse:e"})
        self.assertEqual([x["fonte"] for x in falhas],
                         ["greenhouse:a", "greenhouse:b", "greenhouse:c", "greenhouse:d"])
        for x in falhas:
            with self.subTest(fonte=x["fonte"]):
                self.assertTrue(x["motivo"])

    def test_lista_vazia_nao_e_falha(self):
        self.assertEqual(self.coletar([ACME], Fake({GH_URL.format("acme"): '{"jobs": []}'})), ([], []))

    def test_pausa_de_1_a_2_segundos_entre_chamadas_e_nao_antes_da_primeira(self):
        fontes = [_fonte(t) for t in "abc"]
        fake = Fake({GH_URL.format(t): '{"jobs": []}' for t in "abc"})
        pausas = []
        co.coletar(fontes, fake, sleep=pausas.append)
        self.assertEqual(len(pausas), 2)
        for s in pausas:
            self.assertTrue(1 <= s <= 2, s)

    def test_fonte_de_ats_sem_adaptador_nao_e_consultada(self):
        fake = Fake({})
        self.assertEqual(self.coletar([{**ACME, "ats": "workable", "token": "acme"}], fake), ([], []))
        self.assertEqual(fake.chamadas, [])

    def test_elegibilidade_vem_so_do_texto_de_localizacao(self):
        casos = {"São Paulo, Brasil": "brasil", "Remote - Brazil": "brasil", "Rio de Janeiro": "brasil",
                 "Belo Horizonte, MG": "brasil", "LATAM": "latam", "Latin America": "latam",
                 "Remote": "nao_informada", "Remote - Worldwide": "nao_informada",
                 "London, UK": "nao_informada", "": "nao_informada"}
        for local, esperado in casos.items():
            with self.subTest(local=local):
                self.assertEqual(co.elegibilidade_do_local(local), esperado)

    def test_processar_aplica_as_regras_comuns_as_vagas_da_fonte(self):
        vagas, _ = self.coletar([ACME], Fake({GH_URL.format("acme"): GH_OK}))
        ok, fora = b.processar(vagas, "", desde=date(2026, 11, 1), hoje=HOJE, remoto=True,
                               titulos_excluidos=["Staff"])
        self.assertEqual(ok, [])
        motivos = {d["titulo"]: d["motivo"] for d in fora}
        self.assertEqual(motivos["Engenheiro Backend"], "modalidade não verificada")
        self.assertIn("não confirma", motivos["Backend Engineer"])
        self.assertIn("nível acima", motivos["Staff Engineer"])
        ok, _ = b.processar(vagas[2:], "", desde=date(2026, 11, 1), hoje=HOJE, remoto=True)
        self.assertEqual([v["titulo"] for v in ok], ["Staff Engineer"])

    def test_empresa_excluida_e_descartada_com_motivo(self):
        vagas, _ = self.coletar([ACME], Fake({GH_URL.format("acme"): GH_OK}))
        ok, fora = b.processar(vagas, "Acme\n", desde=date(2026, 11, 1), hoje=HOJE)
        self.assertEqual(ok, [])
        self.assertEqual({d["motivo"] for d in fora}, {"consta em vagas_excluidas.md"})

    def test_data_ausente_vira_sem_data_publicacao(self):
        sem = json.dumps({"jobs": [_gh_job(7, "Dev", "Brasil", publicada=None)]})
        vagas, _ = self.coletar([ACME], Fake({GH_URL.format("acme"): sem}))
        ok, fora = b.processar(vagas, "", desde=date(2026, 11, 1), hoje=HOJE)
        self.assertEqual(ok, [])
        self.assertEqual(fora[0]["motivo"], "sem data de publicação verificada")


LEVER_URL = "https://api.lever.co/v0/postings/{}?mode=json&limit=100"
# 2026-11-05T00:00:00Z em milissegundos (createdAt do Lever é epoch em ms).
LEVER_2026_11_05 = 1793836800000


def _lever_vaga(i, texto, local, criada=LEVER_2026_11_05, atualizada=None):
    return {"id": i, "text": texto, "hostedUrl": f"https://jobs.lever.co/neon/{i}",
            "applyUrl": f"https://jobs.lever.co/neon/{i}/apply", "createdAt": criada,
            "updatedAt": atualizada, "categories": {"location": local, "allLocations": [local]},
            "workplaceType": "remote", "country": "BR", "descriptionPlain": "DESCRIÇÃO COMPLETA NÃO GRAVAR",
            "descriptionBodyPlain": "DESCRIÇÃO COMPLETA NÃO GRAVAR", "additionalPlain": "NÃO GRAVAR"}


# Resposta gravada (fictícia) do endpoint público de postings do Lever (lista em JSON).
LEVER_OK = json.dumps([_lever_vaga("a1", "Engenheiro Backend", "São Paulo, Brasil"),
                       _lever_vaga("a2", "Backend Engineer", "Remoto"),
                       _lever_vaga("a3", "Staff Engineer", "Remote - Brazil", atualizada=1794311022391)])
NEON = {"empresa": "Neon", "ats": "lever", "token": "neon", "evidencia_url": "https://neon.com.br/carreiras",
        "verificado_em": "2026-11-11", "vinculo": "pagina_oficial"}


class ColetaLever(unittest.TestCase):
    def coletar(self, fontes, fake):
        return co.coletar(fontes, fake, pausa=(0, 0), sleep=lambda s: None)

    def test_sucesso_mapeia_para_o_formato_comum(self):
        vagas, falhas = self.coletar([NEON], Fake({LEVER_URL.format("neon"): LEVER_OK}))
        self.assertEqual(falhas, [])
        self.assertEqual([v["titulo"] for v in vagas], ["Engenheiro Backend", "Backend Engineer", "Staff Engineer"])
        v = vagas[0]
        self.assertEqual((v["empresa"], v["link"], v["local"], v["data"]),
                         ("Neon", "https://jobs.lever.co/neon/a1", "São Paulo, Brasil", "2026-11-05"))
        self.assertEqual((v["fonte"], v["candidatura"], v["status"]), ("lever:neon", "externa", "aberta"))
        self.assertEqual((v["elegibilidade"], v["modalidade"]), ("brasil", ""))
        self.assertEqual(vagas[1]["elegibilidade"], "nao_informada")
        self.assertEqual(vagas[1]["modalidade"], "remoto")
        self.assertEqual(b.validar_vagas(vagas), [])

    def test_data_vem_de_created_at_e_nao_da_atualizacao(self):
        vagas, _ = self.coletar([NEON], Fake({LEVER_URL.format("neon"): LEVER_OK}))
        self.assertEqual(vagas[2]["data"], "2026-11-05")

    def test_nao_grava_descricao_completa(self):
        vagas, _ = self.coletar([NEON], Fake({LEVER_URL.format("neon"): LEVER_OK}))
        for v in vagas:
            with self.subTest(titulo=v["titulo"]):
                self.assertNotIn("descriptionPlain", v)
                self.assertFalse(v.get("requisitos"))
                self.assertNotIn("NÃO GRAVAR", json.dumps(v, ensure_ascii=False))

    def test_pede_so_o_token_publico(self):
        fake = Fake({LEVER_URL.format("neon"): LEVER_OK})
        self.coletar([NEON], fake)
        self.assertEqual(fake.chamadas, [LEVER_URL.format("neon")])

    def test_404_e_erro_viram_falha_e_a_rodada_segue(self):
        fontes = [{**NEON, "token": t} for t in ("x", "neon")]
        fake = Fake({
            LEVER_URL.format("x"): urllib.error.HTTPError(LEVER_URL.format("x"), 404, "Not Found", None, None),
            LEVER_URL.format("neon"): LEVER_OK,
        })
        vagas, falhas = self.coletar(fontes, fake)
        self.assertEqual(len(vagas), 3)
        self.assertEqual(falhas, [{"fonte": "lever:x", "motivo": "HTTP 404"}])

    def test_resposta_que_nao_e_lista_vira_falha(self):
        vagas, falhas = self.coletar([NEON], Fake({LEVER_URL.format("neon"): '{"ok": false}'}))
        self.assertEqual(vagas, [])
        self.assertEqual([f["fonte"] for f in falhas], ["lever:neon"])

    def test_lista_vazia_nao_e_falha(self):
        self.assertEqual(self.coletar([NEON], Fake({LEVER_URL.format("neon"): "[]"})), ([], []))

    def test_sem_data_de_criacao_vira_sem_data_publicacao(self):
        sem = json.dumps([_lever_vaga("s1", "Dev", "Brasil", criada=None)])
        vagas, _ = self.coletar([NEON], Fake({LEVER_URL.format("neon"): sem}))
        ok, fora = b.processar(vagas, "", desde=date(2026, 11, 1), hoje=HOJE)
        self.assertEqual(ok, [])
        self.assertEqual(fora[0]["motivo"], "sem data de publicação verificada")

    def test_processar_aplica_as_regras_comuns_as_vagas_do_lever(self):
        vagas, _ = self.coletar([NEON], Fake({LEVER_URL.format("neon"): LEVER_OK}))
        ok, fora = b.processar(vagas, "", desde=date(2026, 11, 1), hoje=HOJE, remoto=True,
                               titulos_excluidos=["Staff"])
        self.assertEqual(ok, [])
        motivos = {d["titulo"]: d["motivo"] for d in fora}
        self.assertEqual(motivos["Engenheiro Backend"], "modalidade não verificada")
        self.assertIn("não confirma", motivos["Backend Engineer"])
        self.assertIn("nível acima", motivos["Staff Engineer"])


ASHBY_URL = "https://api.ashbyhq.com/posting-api/job-board/{}"


def _ab_job(i, titulo, local, *, pais=None, sec=None, remoto=None, modo=None, publicada="2026-10-28T17:26:58.786+00:00"):
    return {"id": f"job-{i}", "title": titulo, "location": local, "secondaryLocations": sec or [],
            "publishedAt": publicada, "isListed": True, "isRemote": remoto, "workplaceType": modo,
            "address": {"postalAddress": {"addressCountry": pais, "addressLocality": local}} if pais else None,
            "jobUrl": f"https://jobs.ashbyhq.com/acme/job-{i}",
            "applyUrl": f"https://jobs.ashbyhq.com/acme/job-{i}/application",
            "descriptionHtml": "<p>DESCRIÇÃO COMPLETA QUE NÃO PODE SER GRAVADA</p>",
            "descriptionPlain": "DESCRIÇÃO COMPLETA QUE NÃO PODE SER GRAVADA"}


def _ab_sec(local, pais):
    return {"location": local, "address": {"postalAddress": {"addressCountry": pais, "addressLocality": local}}}


# Resposta gravada (fictícia, no formato real) do endpoint público de vagas publicadas do Ashby.
ASHBY_OK = json.dumps({"jobs": [
    _ab_job(1, "Engenheiro Backend", "São Paulo", pais="Brazil", remoto=False, modo="Hybrid"),
    _ab_job(2, "Analista Remoto", "Remote", pais="Brazil", remoto=True, modo="Remote"),
    _ab_job(3, "Staff Engineer", "Buenos Aires", pais="Argentina", remoto=True, modo="Hybrid"),
    _ab_job(4, "Platform Engineer", "Remote", remoto=True, modo="Remote"),
    _ab_job(5, "Designer", "Palo Alto", pais="United States", remoto=False, modo="OnSite",
            sec=[_ab_sec("São Paulo", "Brazil")]),
    _ab_job(6, "Data Engineer", "Remote - Brasil", remoto=True, modo=None),
]}, ensure_ascii=False)
ACME_ASHBY = {"empresa": "Acme", "ats": "ashby", "token": "acme", "evidencia_url": ASHBY_URL.format("acme"),
              "verificado_em": "2026-11-11", "vinculo": "conteudo_das_vagas"}


class ColetaAshby(unittest.TestCase):
    def coletar(self, fontes, fake):
        return co.coletar(fontes, fake, pausa=(0, 0), sleep=lambda s: None)

    def vagas_do_acme(self):
        vagas, _ = self.coletar([ACME_ASHBY], Fake({ASHBY_URL.format("acme"): ASHBY_OK}))
        return {v["titulo"]: v for v in vagas}

    def test_sucesso_mapeia_para_o_formato_comum(self):
        vagas, falhas = self.coletar([ACME_ASHBY], Fake({ASHBY_URL.format("acme"): ASHBY_OK}))
        self.assertEqual(falhas, [])
        self.assertEqual(len(vagas), 6)
        v = self.vagas_do_acme()["Engenheiro Backend"]
        self.assertEqual((v["empresa"], v["link"], v["local"], v["data"]),
                         ("Acme", "https://jobs.ashbyhq.com/acme/job-1", "São Paulo", "2026-10-28"))
        self.assertEqual((v["fonte"], v["candidatura"], v["status"]), ("ashby:acme", "externa", "aberta"))
        self.assertEqual(b.validar_vagas(vagas), [])

    def test_vaga_com_isremote_e_endereco_brasileiro_e_aceita(self):
        v = self.vagas_do_acme()["Analista Remoto"]
        self.assertEqual((v["elegibilidade"], v["modalidade"]), ("brasil", "remoto"))
        self.assertEqual(v["evidencia"], "addressCountry: Brazil")

    def test_endereco_estrangeiro_e_sinal_mais_forte_que_o_texto(self):
        v = self.vagas_do_acme()["Staff Engineer"]
        self.assertEqual(v["elegibilidade"], "nao_informada")
        self.assertEqual(v["evidencia"], "addressCountry: Argentina")

    def test_remota_sem_pais_comprovavel_fica_nao_informada(self):
        v = self.vagas_do_acme()["Platform Engineer"]
        self.assertEqual((v["elegibilidade"], v["modalidade"]), ("nao_informada", "remoto"))

    def test_brasil_em_local_secundario_conta_como_elegivel(self):
        v = self.vagas_do_acme()["Designer"]
        self.assertEqual((v["elegibilidade"], v["modalidade"]), ("brasil", "presencial"))
        self.assertEqual(v["evidencia"], "secondaryLocations.addressCountry: Brazil")

    def _uma_vaga(self, **kw):
        resp = json.dumps({"jobs": [_ab_job(9, "Dev Remoto", kw.pop("local", "Remote"), **kw)]}, ensure_ascii=False)
        vagas, _ = self.coletar([ACME_ASHBY], Fake({ASHBY_URL.format("acme"): resp}))
        return vagas[0]

    def test_remota_com_endereco_latam_e_latam(self):
        for pais in ("Mexico", "Colombia", "Argentina"):
            with self.subTest(pais=pais):
                v = self._uma_vaga(pais=pais, remoto=True, modo="Remote")
                self.assertEqual((v["elegibilidade"], v["modalidade"]), ("latam", "remoto"))
                self.assertEqual(v["evidencia"], f"addressCountry: {pais}")

    def test_remota_com_endereco_eua_continua_nao_informada(self):
        v = self._uma_vaga(pais="United States", remoto=True, modo="Remote")
        self.assertEqual(v["elegibilidade"], "nao_informada")

    def test_latam_com_outro_pais_no_texto_do_local_nao_vira_latam(self):
        v = self._uma_vaga(local="Remote - US/Mexico", pais="Mexico", remoto=True, modo="Remote")
        self.assertEqual(v["elegibilidade"], "nao_informada")

    def test_latam_nao_remota_nao_vira_latam(self):
        v = self._uma_vaga(pais="Mexico", remoto=False, modo="OnSite")
        self.assertEqual(v["elegibilidade"], "nao_informada")

    def test_brasil_continua_brasil_mesmo_com_latam_no_secundario(self):
        v = self._uma_vaga(pais="Brazil", remoto=True, modo="Remote", sec=[_ab_sec("Remote", "Mexico")])
        self.assertEqual((v["elegibilidade"], v["evidencia"]), ("brasil", "addressCountry: Brazil"))

    def test_sem_campo_estruturado_usa_o_texto_do_local_como_fallback(self):
        v = self.vagas_do_acme()["Data Engineer"]
        self.assertEqual((v["elegibilidade"], v["modalidade"]), ("brasil", "remoto"))
        self.assertEqual(v["evidencia"], "location: Remote - Brasil")

    def test_data_e_publishedat_e_nao_ha_campo_de_atualizacao_lido(self):
        self.assertTrue(all(v["data"] == "2026-10-28" for v in self.vagas_do_acme().values()))

    def test_nao_grava_descricao_completa(self):
        vagas, _ = self.coletar([ACME_ASHBY], Fake({ASHBY_URL.format("acme"): ASHBY_OK}))
        for v in vagas:
            with self.subTest(titulo=v["titulo"]):
                self.assertNotIn("descriptionHtml", v)
                self.assertNotIn("descriptionPlain", v)
                self.assertNotIn("DESCRIÇÃO", json.dumps(v, ensure_ascii=False))

    def test_pede_so_o_token_publico(self):
        fake = Fake({ASHBY_URL.format("acme"): ASHBY_OK})
        self.coletar([ACME_ASHBY], fake)
        self.assertEqual(fake.chamadas, [ASHBY_URL.format("acme")])

    def test_404_e_json_invalido_viram_falha_e_a_rodada_segue(self):
        fontes = [{**ACME_ASHBY, "token": t} for t in ("a", "b", "c")]
        fake = Fake({
            ASHBY_URL.format("a"): urllib.error.HTTPError(ASHBY_URL.format("a"), 404, "Not Found", None, None),
            ASHBY_URL.format("b"): "<html>não é JSON</html>",
            ASHBY_URL.format("c"): ASHBY_OK,
        })
        vagas, falhas = self.coletar(fontes, fake)
        self.assertEqual(len(vagas), 6)
        self.assertEqual({v["fonte"] for v in vagas}, {"ashby:c"})
        self.assertEqual([(x["fonte"], x["motivo"]) for x in falhas],
                         [("ashby:a", "HTTP 404"), ("ashby:b", "resposta inválida (JSON)")])

    def test_lista_vazia_nao_e_falha(self):
        self.assertEqual(self.coletar([ACME_ASHBY], Fake({ASHBY_URL.format("acme"): '{"jobs": []}'})), ([], []))

    def test_resposta_sem_lista_jobs_e_falha(self):
        vagas, falhas = self.coletar([ACME_ASHBY], Fake({ASHBY_URL.format("acme"): '{"erro": 1}'}))
        self.assertEqual((vagas, [x["motivo"] for x in falhas]), ([], ["resposta inválida (JSON)"]))


class ColetadasNaCli(unittest.TestCase):
    def test_gravar_mescla_vagas_coletadas_e_relata_falhas(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            exc, res, bf = p / "exc.md", p / "res.json", p / "busca.yaml"
            exc.write_text(EXC_OK)
            res.write_text(json.dumps([vaga()]))
            bf.write_text(BUSCA_OK)
            col = p / "coletadas.json"
            col.write_text(json.dumps({
                "vagas": [vaga(titulo="Dev Gh", empresa="Gama Tech", fonte="greenhouse:gama",
                               link="https://job-boards.greenhouse.io/gama/jobs/1")],
                "falhas": [{"fonte": "greenhouse:x", "motivo": "HTTP 404"}]}))
            out = p / "saida"
            r = subprocess.run([sys.executable, str(ROOT / "scripts/busca.py"), "gravar",
                                "--resultados", str(res), "--coletadas", str(col), "--saida-dir", str(out),
                                "--data", "2026-11-08", "--desde", "2026-11-01",
                                "--busca", str(bf), "--excluidas", str(exc)],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            txt = (out / "2026-11-08-busca.md").read_text(encoding="utf-8")
            self.assertIn("Dev Gh", txt)
            self.assertIn("- Fonte: greenhouse:gama", txt)
            self.assertIn("# Tokens com 404", txt)
            self.assertIn("greenhouse:x: HTTP 404", txt)
            self.assertIn("# Resumo da rodada", txt)


class Resumo(unittest.TestCase):
    def setUp(self):
        self.vs = [vaga(titulo="Dev Gh", empresa="Gama", link="https://x/gh1", fonte="greenhouse:gama"),
                   vaga(titulo="Dev Gh 2", empresa="Gama", link="https://x/gh2", fonte="greenhouse:gama"),
                   vaga(titulo="Dev Li", empresa="Beta", link="https://x/li1")]
        self.fora = [{"titulo": "A", "empresa": "Z", "link": "https://x/a",
                      "motivo": "publicada em 2026-10-02, antes de 2026-11-01"},
                     {"titulo": "B", "empresa": "Y", "link": "https://x/b",
                      "motivo": "publicada em 2026-09-30, antes de 2026-11-01"},
                     {"titulo": "C", "empresa": "X", "link": "https://x/c",
                      "motivo": "nível acima do alvo (título contém 'Staff')"}]
        self.falhas = [{"fonte": "greenhouse:velho", "motivo": "HTTP 404"},
                       {"fonte": "ashby:lento", "motivo": "timeout"}]

    def test_conta_mantidas_por_fonte_e_descartes_por_motivo(self):
        txt = b.resumo(self.vs, self.fora, [])
        self.assertIn("- greenhouse: 2", txt)
        self.assertIn("- linkedin: 1", txt)
        self.assertIn("- publicada antes da janela: 2", txt)
        self.assertIn("- nível acima do alvo: 1", txt)

    def test_fonte_com_falha_e_token_404_em_secoes_separadas(self):
        txt = b.resumo(self.vs, self.fora, self.falhas)
        secao_404 = txt.split("# Tokens com 404")[1]
        self.assertIn("- greenhouse:velho: HTTP 404", secao_404)
        self.assertNotIn("ashby:lento", secao_404)
        secao_falha = txt.split("# Fontes com falha")[1].split("# Tokens com 404")[0]
        self.assertIn("- ashby:lento: timeout", secao_falha)
        self.assertNotIn("greenhouse:velho", secao_falha)

    def test_sem_falhas_nao_mostra_secoes_de_falha(self):
        txt = b.resumo(self.vs, self.fora, [])
        self.assertNotIn("# Fontes com falha", txt)
        self.assertNotIn("# Tokens com 404", txt)

    def test_resumo_nao_classifica_nem_recomenda(self):
        txt = b.resumo(self.vs, self.fora, self.falhas).lower()
        for palavra in ("nota", "score", "aderência", "recomend", "melhor", "ordem"):
            self.assertNotIn(palavra, txt)

    def test_render_termina_com_o_resumo_da_rodada(self):
        txt = b.render(self.vs, "2026-11-08", self.fora, DESDE, self.falhas)
        self.assertIn("# Resumo da rodada", txt)
        self.assertIn("# Tokens com 404", txt)
        self.assertLess(txt.index("# Descartadas"), txt.index("# Resumo da rodada"))

    def test_cli_imprime_o_resumo_no_stdout(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            exc, res, bf, col = p / "exc.md", p / "res.json", p / "busca.yaml", p / "col.json"
            exc.write_text(EXC_OK)
            res.write_text(json.dumps([vaga()]))
            bf.write_text(BUSCA_OK)
            col.write_text(json.dumps({"vagas": [], "falhas": [{"fonte": "lever:morto", "motivo": "HTTP 404"}]}))
            r = subprocess.run([sys.executable, str(ROOT / "scripts/busca.py"), "gravar",
                                "--resultados", str(res), "--coletadas", str(col),
                                "--saida-dir", str(p / "s"), "--data", "2026-11-08", "--desde", "2026-11-01",
                                "--busca", str(bf), "--excluidas", str(exc)],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("# Tokens com 404", r.stdout)
            self.assertIn("- lever:morto: HTTP 404", r.stdout)
            self.assertIn("- linkedin: 1", r.stdout)


if __name__ == "__main__":
    unittest.main()


# --- Himalayas (ticket 06): agregador com atribuição, cache de 24 h e paginação por page ---
HIMA_BASE = "https://himalayas.app/jobs/api/search?country=Brazil"
HIMA_WW = "https://himalayas.app/jobs/api/search?worldwide=true"
HIMA_EPOCH = 1794317072  # 2026-11-10 (pubDate)
AGORA = 1794400000  # relógio injetado
DIA = 24 * 3600


def _hima_job(i, restricoes=("Brazil", "Portugal"), **kw):
    return {"title": f"Dev Backend {i}", "companyName": "Lemon", "pubDate": HIMA_EPOCH,
            "expiryDate": HIMA_EPOCH + 30 * DIA, "locationRestrictions": list(restricoes),
            "applicationLink": f"https://himalayas.app/companies/lemon/jobs/{i}?utm_source=api",
            "guid": f"https://himalayas.app/companies/lemon/jobs/{i}",
            "description": "DESCRIÇÃO COMPLETA NÃO PODE SER GRAVADA", "excerpt": "TRECHO NÃO GRAVAR",
            **kw}


def _hima_pagina(jobs, total=None):
    return json.dumps({"offset": 0, "limit": 20, "totalCount": len(jobs) if total is None else total,
                       "jobs": jobs})


class _Rede:
    """Fetch falso: respostas por URL; exceção vira erro; conta as chamadas."""
    def __init__(self, respostas):
        self.respostas, self.chamadas = respostas, []

    def __call__(self, url):
        self.chamadas.append(url)
        r = self.respostas.get(url, _hima_pagina([]))  # sem resposta gravada = página vazia
        if isinstance(r, Exception):
            raise r
        return r


class _Relogio:
    def __init__(self, t=AGORA):
        self.t = t

    def __call__(self):
        return self.t


class HimalayasElegibilidade(unittest.TestCase):
    def elegib(self, restricoes):
        return hm.normalizar(_hima_pagina([_hima_job(1, restricoes)]), _Relogio())[0]["elegibilidade"]

    def test_lista_vazia_e_mundo(self):
        self.assertEqual(self.elegib([]), "mundo")

    def test_com_brazil_e_brasil_mesmo_com_outros_paises(self):
        self.assertEqual(self.elegib(["Brazil"]), "brasil")
        self.assertEqual(self.elegib(["Portugal", "Brazil"]), "brasil")

    def test_so_outros_paises_e_restrita(self):
        self.assertEqual(self.elegib(["Portugal", "Mexico"]), "restrita")


class HimalayasNormalizacao(unittest.TestCase):
    def test_mapeia_link_atribuicao_data_e_metadados(self):
        v = hm.normalizar(_hima_pagina([_hima_job(7)]), _Relogio())[0]
        self.assertEqual(v["titulo"], "Dev Backend 7")
        self.assertEqual(v["empresa"], "Lemon")
        self.assertEqual(v["link"], "https://himalayas.app/companies/lemon/jobs/7?utm_source=api")
        self.assertEqual(v["data"], "2026-11-10")
        self.assertEqual(v["fonte"], "himalayas")
        self.assertEqual(v["atribuicao"], "Fonte: Himalayas")
        self.assertEqual((v["modalidade"], v["candidatura"], v["status"]), ("remoto", "externa", "aberta"))
        self.assertIn("Brazil", v["evidencia"])

    def test_nao_grava_descricao_nem_trecho(self):
        vagas = hm.normalizar(_hima_pagina([_hima_job(1)]), _Relogio())
        gravado = json.dumps(vagas, ensure_ascii=False)
        self.assertNotIn("NÃO PODE", gravado)
        self.assertNotIn("TRECHO", gravado)
        self.assertFalse({"description", "excerpt"} & set(vagas[0]))

    def test_sem_link_de_candidatura_ou_titulo_e_ignorada(self):
        sem_link = {k: v for k, v in _hima_job(2).items() if k != "applicationLink"}
        sem_titulo = {k: v for k, v in _hima_job(3).items() if k != "title"}
        vagas = hm.normalizar(_hima_pagina([sem_link, sem_titulo, _hima_job(4)]), _Relogio())
        self.assertEqual([v["titulo"] for v in vagas], ["Dev Backend 4"])

    def test_expirada_vira_encerrada(self):
        v = hm.normalizar(_hima_pagina([_hima_job(5, expiryDate=AGORA - 1)]), _Relogio())[0]
        self.assertEqual(v["status"], "encerrada")

    def test_json_invalido_ou_sem_lista_levanta_valueerror(self):
        for texto in ("não é json", '{"totalCount": 1}'):
            with self.subTest(texto=texto), self.assertRaises(ValueError):
                hm.normalizar(texto, _Relogio())

    def test_atribuicao_aparece_no_render(self):
        vagas = hm.normalizar(_hima_pagina([_hima_job(1)]), _Relogio())
        txt = b.render(vagas, "2026-11-11", [], DESDE)
        self.assertIn("- Atribuição: Fonte: Himalayas", txt)


class HimalayasColeta(unittest.TestCase):
    def coletar(self, rede, tmp, relogio=None, **kw):
        return hm.coletar(rede, pausa=(0, 0), sleep=lambda s: None, agora=relogio or _Relogio(),
                          cache=Path(tmp) / "himalayas.json", **kw)

    @staticmethod
    def de_brasil(rede):
        return [u for u in rede.chamadas if "worldwide" not in u]

    def test_paginacao_segue_page_ate_o_total_e_pausa_entre_paginas(self):
        p1 = [_hima_job(i) for i in range(20)]
        p2 = [_hima_job(i) for i in range(20, 25)]
        rede = _Rede({HIMA_BASE: _hima_pagina(p1, total=25),
                      HIMA_BASE + "&page=2": _hima_pagina(p2, total=25)})
        pausas = []
        with tempfile.TemporaryDirectory() as d:
            vagas, falhas = hm.coletar(rede, pausa=(1, 2), sleep=pausas.append, agora=_Relogio(),
                                       cache=Path(d) / "himalayas.json")
        self.assertEqual(len(vagas), 25)
        self.assertEqual(falhas, [])
        self.assertEqual(self.de_brasil(rede), [HIMA_BASE, HIMA_BASE + "&page=2"])
        self.assertEqual(len(pausas), 2)  # uma entre as páginas e uma entre as duas consultas
        self.assertTrue(all(1 <= p <= 2 for p in pausas))

    def test_para_no_teto_de_paginas(self):
        rede = _Rede({HIMA_BASE: _hima_pagina([_hima_job(1)], total=999),
                      HIMA_BASE + "&page=2": _hima_pagina([_hima_job(2)], total=999)})
        with tempfile.TemporaryDirectory() as d:
            self.coletar(rede, d, paginas=2)
        self.assertEqual(self.de_brasil(rede), [HIMA_BASE, HIMA_BASE + "&page=2"])

    def test_pagina_vazia_encerra(self):
        rede = _Rede({HIMA_BASE: _hima_pagina([_hima_job(1)], total=50),
                      HIMA_BASE + "&page=2": _hima_pagina([], total=50)})
        with tempfile.TemporaryDirectory() as d:
            vagas, _ = self.coletar(rede, d)
        self.assertEqual(len(vagas), 1)
        self.assertEqual(len(self.de_brasil(rede)), 2)

    def test_erro_de_pagina_vira_falha_mantem_o_que_veio_e_nao_grava_cache(self):
        rede = _Rede({HIMA_BASE: _hima_pagina([_hima_job(1)], total=30),
                      HIMA_BASE + "&page=2": urllib.error.HTTPError(HIMA_BASE, 500, "x", None, None)})
        with tempfile.TemporaryDirectory() as d:
            vagas, falhas = self.coletar(rede, d)
            cache_existe = (Path(d) / "himalayas.json").exists()
        self.assertEqual(len(vagas), 1)
        self.assertEqual(falhas, [{"fonte": "himalayas", "motivo": "HTTP 500"}])
        self.assertFalse(cache_existe)

    def test_primeira_pagina_invalida_vira_falha_sem_vagas(self):
        rede = _Rede({HIMA_BASE: "<html>"})
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(self.coletar(rede, d), ([], [{"fonte": "himalayas",
                                                           "motivo": "resposta inválida (JSON)"}]))

    def test_une_brasil_e_worldwide_sem_repetir_link(self):
        rede = _Rede({HIMA_BASE: _hima_pagina([_hima_job(1), _hima_job(2)]),
                      HIMA_WW: _hima_pagina([_hima_job(2, restricoes=()), _hima_job(3, restricoes=())])})
        with tempfile.TemporaryDirectory() as d:
            vagas, falhas = self.coletar(rede, d)
        self.assertEqual(falhas, [])
        self.assertEqual(len(vagas), 3)
        self.assertEqual({v["titulo"] for v in vagas}, {"Dev Backend 1", "Dev Backend 2", "Dev Backend 3"})
        self.assertEqual({v["titulo"]: v["elegibilidade"] for v in vagas}["Dev Backend 2"], "brasil")

    def test_ordena_por_data_mais_recente_primeiro(self):
        rede = _Rede({HIMA_BASE: _hima_pagina([_hima_job(1, pubDate=HIMA_EPOCH - 5 * DIA),
                                               _hima_job(2, pubDate=HIMA_EPOCH),
                                               _hima_job(3, pubDate=HIMA_EPOCH - DIA)])})
        with tempfile.TemporaryDirectory() as d:
            vagas, _ = self.coletar(rede, d)
        self.assertEqual([v["titulo"] for v in vagas], ["Dev Backend 2", "Dev Backend 3", "Dev Backend 1"])

    def test_para_quando_a_pagina_nao_tem_vaga_na_janela(self):
        rede = _Rede({HIMA_BASE: _hima_pagina([_hima_job(1)], total=999),
                      HIMA_BASE + "&page=2": _hima_pagina([_hima_job(2, pubDate=HIMA_EPOCH - 10 * DIA)], total=999),
                      HIMA_BASE + "&page=3": _hima_pagina([_hima_job(3)], total=999)})
        with tempfile.TemporaryDirectory() as d:
            self.coletar(rede, d, desde=date(2026, 11, 9), paginas=5)
        self.assertEqual(self.de_brasil(rede), [HIMA_BASE, HIMA_BASE + "&page=2"])

    def test_dentro_de_24_h_usa_cache_e_nao_chama_a_rede(self):
        rede = _Rede({HIMA_BASE: _hima_pagina([_hima_job(1)]),
                      HIMA_WW: _hima_pagina([_hima_job(2, restricoes=())])})
        relogio = _Relogio()
        with tempfile.TemporaryDirectory() as d:
            primeira, _ = self.coletar(rede, d, relogio)
            relogio.t += 23 * 3600
            proibida = _Rede({})
            segunda, falhas = self.coletar(proibida, d, relogio)
        self.assertEqual(len(rede.chamadas), 2)
        self.assertEqual(proibida.chamadas, [])  # rede proibida: nenhuma chamada
        self.assertEqual(segunda, primeira)
        self.assertEqual(falhas, [])

    def test_cache_so_vale_para_a_mesma_janela(self):
        rede = _Rede({HIMA_BASE: _hima_pagina([_hima_job(1)])})
        relogio = _Relogio()
        with tempfile.TemporaryDirectory() as d:
            self.coletar(rede, d, relogio, desde=date(2026, 11, 9))
            n = len(rede.chamadas)
            self.coletar(rede, d, relogio, desde=date(2026, 11, 10))
        self.assertGreater(len(rede.chamadas), n)

    def test_depois_de_24_h_chama_a_rede_de_novo(self):
        rede = _Rede({HIMA_BASE: _hima_pagina([_hima_job(1)])})
        relogio = _Relogio()
        with tempfile.TemporaryDirectory() as d:
            self.coletar(rede, d, relogio)
            relogio.t += 25 * 3600
            self.coletar(rede, d, relogio)
        self.assertEqual(len(rede.chamadas), 4)  # duas consultas em cada rodada

    def test_cache_nao_guarda_descricao(self):
        rede = _Rede({HIMA_BASE: _hima_pagina([_hima_job(1)])})
        with tempfile.TemporaryDirectory() as d:
            self.coletar(rede, d)
            conteudo = (Path(d) / "himalayas.json").read_text(encoding="utf-8")
        self.assertNotIn("NÃO PODE", conteudo)
        self.assertNotIn("TRECHO", conteudo)
        self.assertIn("Fonte: Himalayas", conteudo)

    def test_cache_corrompido_e_ignorado(self):
        rede = _Rede({HIMA_BASE: _hima_pagina([_hima_job(1)])})
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "himalayas.json").write_text("{quebrado", encoding="utf-8")
            vagas, _ = self.coletar(rede, d)
        self.assertEqual(len(rede.chamadas), 2)
        self.assertEqual(len(vagas), 1)


class HimalayasDedupe(unittest.TestCase):
    def test_ats_vence_himalayas_na_mesma_vaga(self):
        ats = vaga(titulo="Dev Backend", empresa="Acme", link="https://job-boards.greenhouse.io/acme/jobs/9",
                   fonte="greenhouse:acme")
        hima = vaga(titulo="Dev Backend", empresa="Acme", link="https://himalayas.app/x?utm_source=api",
                    fonte="himalayas", atribuicao="Fonte: Himalayas")
        for ordem in ([ats, hima], [hima, ats]):
            with self.subTest(primeiro=ordem[0]["fonte"]):
                final, fora = b.processar(ordem, "", DESDE, HOJE, remoto=True)
                self.assertEqual([v["link"] for v in final], [ats["link"]])
                self.assertEqual(final[0]["fontes_secundarias"], ["himalayas"])
                self.assertEqual(len(fora), 1)


class HimalayasSemEmpresa(unittest.TestCase):
    def test_vaga_sem_companyname_e_pulada(self):
        sem = _hima_job(1)
        del sem["companyName"]
        vagas = hm.normalizar(_hima_pagina([sem, _hima_job(2)]), _Relogio())
        self.assertEqual([v["titulo"] for v in vagas], ["Dev Backend 2"])

    def test_gravar_com_vaga_do_himalayas_sem_companyname_nao_falha(self):
        sem = _hima_job(1)
        del sem["companyName"]
        vagas = hm.normalizar(_hima_pagina([sem, _hima_job(2)]), _Relogio())
        self.assertEqual(b.validar_vagas(vagas), [])


class ElegibilidadeDoisPaises(unittest.TestCase):
    def test_brasil_mais_outro_pais_explicito_vira_nao_informada(self):
        for local in ("Remote - US (SP office)", "Remote, US or São Paulo", "Remote - Brazil or Portugal",
                      "São Paulo or United Kingdom"):
            with self.subTest(local=local):
                self.assertEqual(co.elegibilidade_do_local(local), "nao_informada")

    def test_casos_existentes_continuam(self):
        casos = {"São Paulo, Brazil": "brasil", "Brazil": "brasil", "São Paulo, Brasil": "brasil",
                 "Remote - Brazil": "brasil", "LATAM": "latam"}
        for local, esperado in casos.items():
            with self.subTest(local=local):
                self.assertEqual(co.elegibilidade_do_local(local), esperado)


class PausaAntesDoHimalayas(unittest.TestCase):
    def test_pausa_entre_ultimo_ats_e_primeira_chamada_do_himalayas(self):
        eventos = []

        def fetch(url):
            eventos.append(("get", url))
            if "greenhouse" in url:
                return GH_OK
            return _hima_pagina([_hima_job(1)])

        with tempfile.TemporaryDirectory() as d:
            vagas, falhas = b.coletar_todas([ACME], fetch=fetch, sleep=lambda s: eventos.append(("sleep", s)),
                                            cache=Path(d) / "himalayas.json")
        self.assertEqual(falhas, [])
        self.assertEqual([e[0] for e in eventos], ["get", "sleep", "get", "sleep", "get"])
        self.assertIn("greenhouse", eventos[0][1])
        self.assertIn("himalayas", eventos[2][1])
        self.assertTrue(1 <= eventos[1][1] <= 2)

    def test_sem_ats_nao_ha_pausa_antes_do_himalayas(self):
        eventos = []

        def fetch(url):
            eventos.append(("get", url))
            return _hima_pagina([_hima_job(1)])

        with tempfile.TemporaryDirectory() as d:
            b.coletar_todas([], fetch=fetch, sleep=lambda s: eventos.append(("sleep", s)),
                            cache=Path(d) / "himalayas.json")
        self.assertEqual([e[0] for e in eventos], ["get", "sleep", "get"])  # pausa entre as consultas


class JanelaNaColeta(unittest.TestCase):
    def test_coletar_todas_repassa_a_janela_ao_himalayas(self):
        rede = _Rede({HIMA_BASE: _hima_pagina([_hima_job(1)], total=999),
                      HIMA_BASE + "&page=2": _hima_pagina([_hima_job(2, pubDate=HIMA_EPOCH - 10 * DIA)], total=999),
                      HIMA_BASE + "&page=3": _hima_pagina([_hima_job(3)], total=999)})
        with tempfile.TemporaryDirectory() as d:
            b.coletar_todas([], fetch=rede, sleep=lambda s: None, cache=Path(d) / "himalayas.json",
                            desde=date(2026, 11, 9))
        self.assertNotIn(HIMA_BASE + "&page=3", rede.chamadas)


class MotivoPublico(unittest.TestCase):
    def test_motivo_da_falha_e_publico(self):
        self.assertEqual(co.motivo_da_falha(urllib.error.HTTPError("u", 500, "x", None, None)), "HTTP 500")
        self.assertFalse(hasattr(co, "_motivo"))
