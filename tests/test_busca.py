"""Testes do /busca (scripts/busca.py). Fixtures fictícias em diretório temporário.
Seams: janela_desde(), build_urls(), processar() (descartes), render() e a CLI (gate, arquivo)."""
import json, subprocess, sys, tempfile, unittest, urllib.error
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
    """Ticket 05: mesma vaga em duas fontes aparece uma vez, com o link da fonte prioritária; rodízio sob o teto."""
    LI = "https://www.linkedin.com/jobs/view/4487014884/"
    ATS = "https://jobs.example.com/beta/jobs/555"

    def test_rebase_vence_linkedin_quando_o_linkedin_vem_primeiro(self):
        li = vaga(link=self.LI, fonte="linkedin")
        ats = vaga(link=self.ATS, fonte="rebase", candidatura="externa")
        ok, fora = b.processar([li, ats], "")
        self.assertEqual([v["link"] for v in ok], [self.ATS])
        self.assertEqual(ok[0]["fontes_secundarias"], ["linkedin"])
        self.assertIn("duplicada", fora[0]["motivo"])
        self.assertEqual(fora[0]["link"], self.LI)

    def test_rebase_vence_linkedin_quando_o_rebase_vem_primeiro(self):
        ats = vaga(link=self.ATS, fonte="rebase", candidatura="externa")
        li = vaga(link=self.LI, fonte="linkedin")
        ok, fora = b.processar([ats, li], "")
        self.assertEqual([v["link"] for v in ok], [self.ATS])
        self.assertEqual(ok[0]["fontes_secundarias"], ["linkedin"])
        self.assertEqual(len(fora), 1)

    def test_linkedin_sem_campo_fonte_conta_como_linkedin(self):
        li = vaga(link=self.LI)  # vaga antiga, sem "fonte"
        ats = vaga(link=self.ATS, fonte="rebase", candidatura="externa")
        ok, _ = b.processar([li, ats], "")
        self.assertEqual([v["link"] for v in ok], [self.ATS])
        self.assertEqual(ok[0]["fontes_secundarias"], ["linkedin"])

    def test_duplicata_entre_linkedin_e_outra_fonte_nao_rebase_mantem_a_primeira(self):
        li = vaga(link=self.LI)
        outra = vaga(link="https://jobs.example.com/beta-dev", fonte="outra")
        ok, fora = b.processar([li, outra], "")
        self.assertEqual([v["link"] for v in ok], [self.LI])
        self.assertEqual(ok[0]["fontes_secundarias"], ["outra"])
        self.assertEqual(len(fora), 1)

    def test_mesmo_link_com_query_diferente_e_duplicata(self):
        a = vaga(titulo="Dev A", link="https://jobs.example.com/beta/jobs/555?gh_src=x", fonte="rebase")
        c = vaga(titulo="Dev B", link="https://jobs.example.com/beta/jobs/555?utm=1", fonte="rebase")
        self.assertEqual(len(b.processar([a, c], "")[0]), 1)

    def test_rodizio_divide_o_teto_entre_fontes(self):
        li = [vaga(titulo=f"LI {i}", link=f"https://www.linkedin.com/jobs/view/{100000 + i}/", fonte="linkedin")
              for i in range(5)]
        gh = [vaga(titulo=f"GH {i}", empresa=f"Emp {i}", link=f"https://jobs.example.com/e/jobs/{i}",
                   fonte="rebase", candidatura="externa") for i in range(5)]
        ok, fora = b.processar(li + gh, "", maximo=4)
        self.assertEqual([v["titulo"] for v in ok], ["LI 0", "LI 1", "GH 0", "GH 1"])
        self.assertEqual(len(fora), 6)
        self.assertTrue(all("rodízio" in d["motivo"] for d in fora[-6:]))

    def test_fonte_com_pouca_vaga_repassa_a_sobra_a_outra(self):
        li = [vaga(titulo=f"LI {i}", link=f"https://www.linkedin.com/jobs/view/{100000 + i}/") for i in range(5)]
        gh = [vaga(titulo="GH 0", empresa="Emp 0", link="https://jobs.example.com/e/jobs/0",
                   fonte="rebase", candidatura="externa")]
        ok, _ = b.processar(li + gh, "", maximo=4)
        self.assertEqual(sorted(v["titulo"] for v in ok), ["GH 0", "LI 0", "LI 1", "LI 2"])

    def test_rodizio_nao_muda_a_ordem_quando_ha_so_uma_fonte(self):
        vs = [vaga(titulo=f"Vaga {i}", link=f"https://x/{i}") for i in range(1, 5)]
        ok, _ = b.processar(vs, "", maximo=2)
        self.assertEqual([v["titulo"] for v in ok], ["Vaga 1", "Vaga 2"])

    def test_render_mostra_fontes_secundarias(self):
        ats = vaga(link=self.ATS, fonte="rebase", candidatura="externa")
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

    def test_trecho_mostra_requisitos_e_trecho_juntos(self):
        v = vaga(requisitos="Python, Django", trecho="Salário R$ 12.000")
        txt = b.render([v], "2026-11-08", [], DESDE)
        self.assertIn("- Trecho: Python, Django — Salário R$ 12.000", txt)

    def test_trecho_so_com_o_que_existir_sem_separador_sobrando(self):
        so_req = b.render([vaga(requisitos="Python", trecho="")], "2026-11-08", [], DESDE)
        self.assertIn("- Trecho: Python\n", so_req)
        so_trecho = b.render([vaga(requisitos="", trecho="Salário R$ 12.000")], "2026-11-08", [], DESDE)
        self.assertIn("- Trecho: Salário R$ 12.000\n", so_trecho)
        self.assertNotIn("—  ", so_trecho)
        self.assertNotIn(" — \n", so_req + so_trecho)

    def test_data_do_rebase_diz_entrou_no_rebase_em(self):
        txt = b.render([vaga(fonte="rebase", data="2026-11-05")], "2026-11-08", [], DESDE)
        self.assertIn("- Data: entrou no Rebase em 2026-11-05", txt)

    def test_data_das_outras_fontes_continua_como_antes(self):
        txt = b.render([vaga(fonte="outra:acme", data="2026-11-05")], "2026-11-08", [], DESDE)
        self.assertIn("- Data: 2026-11-05", txt)
        self.assertNotIn("entrou no Rebase", txt)


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

    def test_candidatos_coletadas_corta_o_que_o_rebase_ja_trouxe(self):
        itens = [{"origem": "A", "id": "1", "titulo": "Backend Engineer", "empresa": "Zeta Labs"},
                 {"origem": "A", "id": "2", "titulo": "  backend   ENGINEER ", "empresa": "ZETA LABS "},
                 {"origem": "B", "id": "3", "titulo": "Backend Engineer", "empresa": "Outra SA"},
                 {"origem": "B", "id": "4", "titulo": "Dev Pleno", "empresa": "Zeta Labs"}]
        lst = self.p / "lst.json"
        lst.write_text(json.dumps(itens))
        col = self.p / "col.json"
        col.write_text(json.dumps({"vagas": [vaga(titulo="Backend Engineer", empresa="Zeta Labs", fonte="rebase")],
                                   "falhas": []}))
        r = self.run_cli("candidatos", "--listagens", str(lst), "--coletadas", str(col))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual([i["id"] for i in json.loads(r.stdout)], ["3", "4"])
        self.assertEqual(r.stderr.count("já veio do Rebase"), 2)
        self.assertIn("Backend Engineer | Zeta Labs", r.stderr)

    def test_candidatos_sem_coletadas_nao_corta_nada(self):
        itens = [{"origem": "A", "id": "1", "titulo": "Backend Engineer", "empresa": "Zeta Labs"}]
        lst = self.p / "lst.json"
        lst.write_text(json.dumps(itens))
        r = self.run_cli("candidatos", "--listagens", str(lst))
        self.assertEqual(len(json.loads(r.stdout)), 1)
        self.assertNotIn("já veio do Rebase", r.stderr)

    def test_candidatos_coletadas_sem_vagas_do_rebase_nao_corta(self):
        itens = [{"origem": "A", "id": "1", "titulo": "Backend Engineer", "empresa": "Zeta Labs"}]
        lst = self.p / "lst.json"
        lst.write_text(json.dumps(itens))
        col = self.p / "col.json"
        col.write_text(json.dumps({"vagas": [], "falhas": [{"fonte": "rebase", "motivo": "401"}]}))
        r = self.run_cli("candidatos", "--listagens", str(lst), "--coletadas", str(col))
        self.assertEqual(len(json.loads(r.stdout)), 1)

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
                "vagas": [vaga(titulo="Dev Gh", empresa="Gama Tech", fonte="outra:gama",
                               link="https://jobs.example.com/gama/jobs/1")],
                "falhas": [{"fonte": "outra:x", "motivo": "HTTP 404"}]}))
            out = p / "saida"
            r = subprocess.run([sys.executable, str(ROOT / "scripts/busca.py"), "gravar",
                                "--resultados", str(res), "--coletadas", str(col), "--saida-dir", str(out),
                                "--data", "2026-11-08", "--desde", "2026-11-01",
                                "--busca", str(bf), "--excluidas", str(exc)],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            txt = (out / "2026-11-08-busca.md").read_text(encoding="utf-8")
            self.assertIn("Dev Gh", txt)
            self.assertIn("- Fonte: outra:gama", txt)
            self.assertIn("outra:x: HTTP 404", txt)
            self.assertIn("# Resumo da rodada", txt)


class DescartesDaColeta(unittest.TestCase):
    def test_saida_da_coleta_leva_descartadas_do_adaptador(self):
        r = {"vagas": [vaga()], "falhas": [],
             "descartadas": [{"titulo": "Sr", "empresa": "Omega", "link": "https://x/o",
                              "motivo": "nível acima do alvo (sênior)"}]}
        out = b.saida_coleta(r)
        self.assertEqual(set(out), {"vagas", "falhas", "descartadas"})
        self.assertEqual(out["descartadas"], r["descartadas"])

    def test_gravar_leva_descartadas_do_rebase_para_a_secao_e_ao_resumo(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            exc, res, bf = p / "exc.md", p / "res.json", p / "busca.yaml"
            exc.write_text(EXC_OK)
            res.write_text(json.dumps([vaga()]))
            bf.write_text(BUSCA_OK)
            col = p / "coletadas.json"
            col.write_text(json.dumps({
                "vagas": [],
                "falhas": [],
                "descartadas": [{"titulo": "Sr Dev", "empresa": "Omega", "link": "https://x/o",
                                 "motivo": "nível acima do alvo (sênior)"},
                                {"titulo": "Dev", "empresa": "Psi", "link": "https://x/p",
                                 "motivo": "sem apply_url (candidatura no ATS)"}]}))
            out = p / "saida"
            r = subprocess.run([sys.executable, str(ROOT / "scripts/busca.py"), "gravar",
                                "--resultados", str(res), "--coletadas", str(col), "--saida-dir", str(out),
                                "--data", "2026-11-08", "--desde", "2026-11-01",
                                "--busca", str(bf), "--excluidas", str(exc)],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            txt = (out / "2026-11-08-busca.md").read_text(encoding="utf-8")
            secao = txt.split("# Descartadas", 1)[1]
            self.assertIn("Sr Dev | Omega | nível acima do alvo (sênior) | https://x/o", secao)
            self.assertIn("Dev | Psi | sem apply_url (candidatura no ATS) | https://x/p", secao)
            self.assertIn("- nível acima do alvo: 1", txt)
            self.assertIn("- sem apply_url: 1", txt)


class Resumo(unittest.TestCase):
    def setUp(self):
        self.vs = [vaga(titulo="Dev Gh", empresa="Gama", link="https://x/gh1", fonte="outra:gama"),
                   vaga(titulo="Dev Gh 2", empresa="Gama", link="https://x/gh2", fonte="outra:gama"),
                   vaga(titulo="Dev Li", empresa="Beta", link="https://x/li1")]
        self.fora = [{"titulo": "A", "empresa": "Z", "link": "https://x/a",
                      "motivo": "publicada em 2026-10-02, antes de 2026-11-01"},
                     {"titulo": "B", "empresa": "Y", "link": "https://x/b",
                      "motivo": "publicada em 2026-09-30, antes de 2026-11-01"},
                     {"titulo": "C", "empresa": "X", "link": "https://x/c",
                      "motivo": "nível acima do alvo (título contém 'Staff')"}]
        self.falhas = [{"fonte": "outra:velho", "motivo": "HTTP 404"},
                       {"fonte": "lenta:lento", "motivo": "timeout"}]

    def test_conta_mantidas_por_fonte_e_descartes_por_motivo(self):
        txt = b.resumo(self.vs, self.fora, [])
        self.assertIn("- outra: 2", txt)
        self.assertIn("- linkedin: 1", txt)
        self.assertIn("- publicada antes da janela: 2", txt)
        self.assertIn("- nível acima do alvo: 1", txt)

    def test_todas_as_falhas_em_fontes_com_falha_sem_secao_de_404(self):
        txt = b.resumo(self.vs, self.fora, self.falhas)
        secao_falha = txt.split("# Fontes com falha")[1]
        self.assertIn("- outra:velho: HTTP 404", secao_falha)
        self.assertIn("- lenta:lento: timeout", secao_falha)
        self.assertNotIn("Tokens com 404", txt)

    def test_sem_falhas_nao_mostra_secoes_de_falha(self):
        txt = b.resumo(self.vs, self.fora, [])
        self.assertNotIn("# Fontes com falha", txt)

    def test_resumo_nao_classifica_nem_recomenda(self):
        txt = b.resumo(self.vs, self.fora, self.falhas).lower()
        for palavra in ("nota", "score", "aderência", "recomend", "melhor", "ordem"):
            self.assertNotIn(palavra, txt)

    def test_render_termina_com_o_resumo_da_rodada(self):
        txt = b.render(self.vs, "2026-11-08", self.fora, DESDE, self.falhas)
        self.assertIn("# Resumo da rodada", txt)
        self.assertIn("# Fontes com falha", txt)
        self.assertLess(txt.index("# Descartadas"), txt.index("# Resumo da rodada"))

    def test_cli_imprime_o_resumo_no_stdout(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            exc, res, bf, col = p / "exc.md", p / "res.json", p / "busca.yaml", p / "col.json"
            exc.write_text(EXC_OK)
            res.write_text(json.dumps([vaga()]))
            bf.write_text(BUSCA_OK)
            col.write_text(json.dumps({"vagas": [], "falhas": [{"fonte": "outra:morto", "motivo": "HTTP 404"}]}))
            r = subprocess.run([sys.executable, str(ROOT / "scripts/busca.py"), "gravar",
                                "--resultados", str(res), "--coletadas", str(col),
                                "--saida-dir", str(p / "s"), "--data", "2026-11-08", "--desde", "2026-11-01",
                                "--busca", str(bf), "--excluidas", str(exc)],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("# Fontes com falha", r.stdout)
            self.assertIn("- outra:morto: HTTP 404", r.stdout)
            self.assertIn("- linkedin: 1", r.stdout)


if __name__ == "__main__":
    unittest.main()
