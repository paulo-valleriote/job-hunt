"""Testes da lista de tokens (fontes_ats.json) sem rede: acréscimo só com aprovação explícita."""
import json, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import fontes  # noqa: E402

NOVA = {
    "empresa": "Exemplo SA", "ats": "greenhouse", "token": "exemplo",
    "evidencia_url": "https://exemplo.com.br/carreiras",
    "verificado_em": "2026-11-11", "vinculo": "pagina_oficial",
}


class Acrescentar(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.arq = Path(self.dir.name) / "fontes_ats.json"
        self.arq.write_text(json.dumps([], ensure_ascii=False), encoding="utf-8")

    def tearDown(self):
        self.dir.cleanup()

    def _lista(self):
        return json.loads(self.arq.read_text(encoding="utf-8"))

    def test_sem_aprovacao_explicita_nada_e_gravado(self):
        with self.assertRaises(fontes.SemAprovacao):
            fontes.acrescentar(NOVA, aprovado=False, arquivo=self.arq)
        self.assertEqual(self._lista(), [])

    def test_aprovada_e_valida_entra_na_lista(self):
        fontes.acrescentar(NOVA, aprovado=True, arquivo=self.arq)
        self.assertEqual(self._lista(), [NOVA])

    def test_sem_evidencia_e_recusada(self):
        sem_evidencia = {**NOVA, "evidencia_url": ""}
        with self.assertRaises(ValueError) as ctx:
            fontes.acrescentar(sem_evidencia, aprovado=True, arquivo=self.arq)
        self.assertIn("evidencia_url", str(ctx.exception))
        self.assertEqual(self._lista(), [])

    def test_vinculo_invalido_e_recusado(self):
        with self.assertRaises(ValueError):
            fontes.acrescentar({**NOVA, "vinculo": "palpite"}, aprovado=True, arquivo=self.arq)
        self.assertEqual(self._lista(), [])

    def test_evidencia_que_nao_e_https_e_recusada(self):
        with self.assertRaises(ValueError) as ctx:
            fontes.acrescentar({**NOVA, "evidencia_url": "exemplo.com.br/carreiras"},
                               aprovado=True, arquivo=self.arq)
        self.assertIn("https", str(ctx.exception))
        self.assertEqual(self._lista(), [])

    def test_mesmo_ats_e_token_ja_existente_e_recusado(self):
        fontes.acrescentar(NOVA, aprovado=True, arquivo=self.arq)
        with self.assertRaises(ValueError) as ctx:
            fontes.acrescentar({**NOVA, "empresa": "Outra"}, aprovado=True, arquivo=self.arq)
        self.assertIn("já existe", str(ctx.exception))
        self.assertEqual(len(self._lista()), 1)

    def test_chave_desconhecida_e_recusada(self):
        with self.assertRaises(ValueError) as ctx:
            fontes.acrescentar({**NOVA, "cpf": "000"}, aprovado=True, arquivo=self.arq)
        self.assertIn("chave desconhecida", str(ctx.exception))
        self.assertEqual(self._lista(), [])


class Cli(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.arq = Path(self.dir.name) / "fontes_ats.json"
        self.arq.write_text("[]", encoding="utf-8")

    def tearDown(self):
        self.dir.cleanup()

    def test_cli_sem_flag_de_aprovacao_nao_grava(self):
        codigo = fontes.main(["acrescentar", "--json", json.dumps(NOVA), "--arquivo", str(self.arq)])
        self.assertNotEqual(codigo, 0)
        self.assertEqual(json.loads(self.arq.read_text(encoding="utf-8")), [])

    def test_cli_com_aprovacao_grava(self):
        codigo = fontes.main(["acrescentar", "--json", json.dumps(NOVA),
                              "--arquivo", str(self.arq), "--aprovado"])
        self.assertEqual(codigo, 0)
        self.assertEqual(json.loads(self.arq.read_text(encoding="utf-8")), [NOVA])


if __name__ == "__main__":
    unittest.main()
