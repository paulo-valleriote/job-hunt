# 01: Lista de tokens com evidência e fonte nas vagas gravadas

**What to build:** o arquivo versionado de empresas e tokens de ATS (sem dado pessoal), com `empresa`, `ats`, `token`, `evidencia_url`, `verificado_em` e o tipo de vínculo (página oficial da empresa aponta o ATS, ou confirmado só pelo conteúdo das vagas). A lista inicial traz os dez tokens testados na pesquisa (Greenhouse: ebanx, quintoandar, stone, gympass, vtex, inter, c6bank, rdstation; Ashby: nubank; Lever: neon). Entrada sem evidência é recusada. O contrato do `gravar` passa a aceitar `fonte` e a atribuição, continua recusando chave desconhecida, e o `render` mostra a fonte em cada vaga. A tela Vagas continua lendo o arquivo gravado. É o prefactor dos demais tickets: deixa pronto o formato comum de vaga.

**Blocked by:** None (can start immediately)

**Status:** resolved

- [ ] A lista traz os dez tokens iniciais, cada um com evidência, data de verificação e tipo de vínculo (só Ebanx e Neon como página oficial; os demais como conteúdo das vagas)
- [ ] Entrada de token sem evidência é recusada
- [ ] `gravar` aceita `fonte` e atribuição e segue recusando chave desconhecida
- [ ] `render` mostra a fonte (e a atribuição, quando houver) em cada vaga
- [ ] Testes em `make test-busca`, no estilo de `tests/test_busca.py`; `tests/test_ui_vagas.py` continua passando

## Comments

Implementado na branch `integration/fontes-gratuitas-vagas`.
