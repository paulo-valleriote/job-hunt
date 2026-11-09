"""Testes de scripts/linkedin_vaga.js: leitura da página de uma vaga do LinkedIn.
A função é pura (texto da página -> campos); roda no navegador via evaluate_script e aqui via `node`.
Fixtures fictícias que copiam a estrutura das páginas reais, incluindo o card lateral "Mais vagas"."""
import json, shutil, subprocess, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JS = ROOT / "scripts" / "linkedin_vaga.js"
AGORA = "2026-11-09T08:00:00"


def pagina(cabecalho, titulo="Dev Backend Go", descricao="Requisitos\nExperiência com Go\nPostgreSQL",
           lateral="Gama\nBrasil (Remoto)\n1 conexão trabalha aqui\nPromovida\n·\nAnunciada há 2 semanas"):
    return "\n".join(["Reative Premium: 50% de desconto", "Empresa Beta", titulo, cabecalho,
                      "Use a IA para avaliar a adequação do seu perfil", "Sobre a vaga", descricao,
                      "Mais vagas", lateral])


@unittest.skipUnless(shutil.which("node"), "node não instalado")
class LeituraDaVaga(unittest.TestCase):
    def le(self, texto, links=("Candidatar-se",), titulo="Dev Backend Go", agora=AGORA):
        r = subprocess.run(["node", str(JS)], capture_output=True, text=True, timeout=20,
                           input=json.dumps({"texto": texto, "links": list(links), "titulo": titulo, "agora": agora}))
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)

    def test_data_vem_do_cabecalho_e_ignora_o_card_lateral(self):
        t = pagina("Brasil · Compartilhada há 1 dia · Mais de 100 pessoas clicaram em Candidate-se\nRemoto\nTempo integral")
        self.assertEqual(self.le(t)["data"], "2026-11-08")  # não "há 2 semanas" do card "Mais vagas"

    def test_formato_sem_prefixo_e_conversao_de_horas_para_o_dia(self):
        for cab, esperado in (("Estados Unidos · há 1 hora · 17 candidaturas", "2026-11-09"),
                              ("Brasil · Compartilhada há 20 horas · 3 candidaturas", "2026-11-08"),
                              ("Brasil · Anunciada há 3 semanas · 3 candidaturas", "2026-10-19")):
            with self.subTest(cab=cab):
                self.assertEqual(self.le(pagina(cab + "\nRemoto"))["data"], esperado)

    def test_sem_data_no_cabecalho_devolve_nulo_mesmo_com_data_no_card_lateral(self):
        # Caso real (Descartes): cabeçalho sem data; só o card "Mais vagas" tinha "há 2 semanas".
        self.assertIsNone(self.le(pagina("Brasil (Remoto)\nCandidatar-se"))["data"])

    def test_tipo_de_candidatura_pelos_botoes(self):
        t = pagina("Brasil · há 1 dia\nRemoto")
        self.assertEqual(self.le(t, links=["Candidatura simplificada", "Salvar"])["candidatura"], "simplificada")
        self.assertEqual(self.le(t, links=["Easy Apply"])["candidatura"], "simplificada")
        self.assertEqual(self.le(t, links=["Candidatar-se no site da empresa", "Candidatar-se"])["candidatura"], "externa")
        self.assertIsNone(self.le(t, links=["Salvar"])["candidatura"])

    def test_modalidade_e_local_vem_do_cabecalho(self):
        for linha, mod in (("Remoto", "remoto"), ("Híbrido", "hibrido"), ("Presencial", "presencial")):
            with self.subTest(mod=mod):
                r = self.le(pagina(f"São Paulo e Região · há 1 dia · 4 candidaturas\n{linha}\nTempo integral"))
                self.assertEqual((r["modalidade"], r["local"]), (mod, "São Paulo e Região"))
        r = self.le(pagina("Brasil · há 1 dia"))
        self.assertEqual(r["modalidade"], "")  # não mostrou: o /busca deixa vazio e a vaga é descartada

    def test_modalidade_do_card_lateral_nao_vale(self):
        t = pagina("Brasil · há 1 dia", lateral="Gama\nBrasil · Presencial\nHíbrido")
        self.assertEqual(self.le(t)["modalidade"], "")

    def test_status_encerrada_so_se_o_cabecalho_avisa(self):
        self.assertEqual(self.le(pagina("Brasil · há 1 dia\nNão aceita mais candidaturas"))["status"], "encerrada")
        self.assertEqual(self.le(pagina("Brasil · há 1 dia\nNo longer accepting applications"))["status"], "encerrada")
        t = pagina("Brasil · há 1 dia\nRemoto", lateral="Gama\nNão aceita mais candidaturas")
        self.assertEqual(self.le(t)["status"], "aberta")

    def test_titulo_com_remote_nao_decide_a_modalidade(self):
        titulo = "Go Developer (Remote)"
        t = pagina("Reino Unido · há 2 horas\nHíbrido", titulo=titulo)
        self.assertEqual(self.le(t, titulo=titulo)["modalidade"], "hibrido")

    def test_pistas_de_elegibilidade_da_descricao_e_nao_do_card_lateral(self):
        desc = ("About us\nWe build payment APIs.\nThis role is fully remote across Latin America.\n"
                "Candidates must be authorized to work in the US.\nGood English.")
        t = pagina("Estados Unidos · há 1 dia\nRemoto", descricao=desc,
                   lateral="Gama\nRemote - worldwide\nPromovida")
        pistas = self.le(t)["pistas"]
        self.assertEqual(pistas, ["This role is fully remote across Latin America.",
                                  "Candidates must be authorized to work in the US."])

    def test_sem_pista_devolve_lista_vazia(self):
        self.assertEqual(self.le(pagina("Brasil · há 1 dia"))["pistas"], [])

    def test_requisitos_sao_as_linhas_sob_o_titulo(self):
        for titulo_req in ("Requisitos", "Requirements", "What We Are Looking For In You", "Qualifications"):
            with self.subTest(titulo=titulo_req):
                desc = f"Sobre nós\nSomos uma empresa.\n{titulo_req}\nGo em produção\nPostgreSQL\nKubernetes\nInglês\nExtra\nBenefícios\nVR"
                r = self.le(pagina("Brasil · há 1 dia", descricao=desc))
                self.assertEqual(r["requisitos"], ["Go em produção", "PostgreSQL", "Kubernetes", "Inglês"])

    def test_sem_titulo_de_requisitos_devolve_vazio_em_vez_de_inventar(self):
        r = self.le(pagina("Brasil · há 1 dia", descricao="Somos uma empresa.\nVenha crescer."))
        self.assertEqual(r["requisitos"], [])

    def test_titulos_de_requisitos_em_portugues_da_pagina_real(self):
        for titulo_req in ("O Que Esperamos De Você", "O que buscamos", "Pré-requisitos"):
            with self.subTest(titulo=titulo_req):
                desc = f"Sobre a vaga\n{titulo_req}\nGo em produção\nPostgreSQL"
                self.assertEqual(self.le(pagina("Brasil · há 1 dia", descricao=desc))["requisitos"],
                                 ["Go em produção", "PostgreSQL"])

    def test_texto_institucional_da_empresa_nao_vira_pista(self):
        # Caso real (Stone): "Sobre a empresa" cita "Brasil" em todo parágrafo e não diz nada da vaga.
        desc = ("Requisitos\nGo\nSobre a empresa\nSomos a maior empresa independente de pagamentos do Brasil.")
        r = self.le(pagina("Brasil · há 1 dia", descricao=desc))
        self.assertEqual(r["pistas"], [])
        self.assertEqual(r["requisitos"], ["Go"])

    def test_pode_ser_avaliado_duas_vezes_na_mesma_pagina(self):
        # No navegador o arquivo roda como script clássico: const/function no topo vazariam para o
        # escopo global e a 2ª avaliação (mesma aba) falharia com "already been declared".
        js = ("const vm=require('vm'),fs=require('fs');"
              "const ctx=vm.createContext({document:{body:{innerText:process.argv[2]},title:'Dev Backend Go | Beta | LinkedIn',"
              "querySelectorAll:()=>[]}});"
              "const src=fs.readFileSync(process.argv[1],'utf8');"
              "vm.runInContext(src,ctx);console.log(JSON.stringify(vm.runInContext(src,ctx)));")
        texto = pagina("Brasil · há 1 dia\nRemoto")
        r = subprocess.run(["node", "-e", js, str(JS), texto], capture_output=True, text=True, timeout=20)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["modalidade"], "remoto")

    def test_brasil_solto_no_texto_institucional_nao_e_pista_mas_com_sinal_de_elegibilidade_e(self):
        # Caso real (Stone): a descrição abre com "Sobre a Stone", cheia de "Brasil"/"brasileiro".
        desc = ("Sobre a Beta\nSomos a maior empresa independente de pagamentos do Brasil.\n"
                "Servindo o empreendedor brasileiro.\nRequisitos\nGo\n"
                "Vaga remota para candidatos residentes no Brasil.\nRemote in Brazil only.")
        pistas = self.le(pagina("Brasil · há 1 dia", descricao=desc))["pistas"]
        self.assertEqual(pistas, ["Vaga remota para candidatos residentes no Brasil.", "Remote in Brazil only."])


if __name__ == "__main__":
    unittest.main()
