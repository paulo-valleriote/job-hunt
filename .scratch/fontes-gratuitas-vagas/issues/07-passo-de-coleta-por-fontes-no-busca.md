# 07: Passo de coleta por fontes no `/busca`

**What to build:** o comando `/busca` roda a coleta por fontes e a do LinkedIn pelo navegador, e junta o resultado num único arquivo do dia, com `fonte` em cada vaga. Definir a ordem entre as duas coletas (questão aberta 5). O LinkedIn segue só pelo navegador e a coleta das fontes roda sem navegador e sem login. O `/busca` continua recusando rodar com `busca.yaml` ou `vagas_excluidas.md` incompletos, valendo também para as fontes novas. Vagas de ATS caem no grupo "Candidatura externa". Nada de `private/` em commit ou consulta externa. A mudança na instrução ao agente segue as boas práticas de escrita para agentes (skill `writing-for-agents`).

**Blocked by:** 05, 06

**Status:** resolved

- [ ] `/busca` produz um único arquivo do dia com vagas do LinkedIn e das fontes novas
- [ ] O gate de configuração incompleta continua barrando antes de qualquer coleta
- [ ] Ordem das coletas definida e documentada no comando
- [ ] Vagas de ATS aparecem em "Candidatura externa"
- [ ] A tela Vagas continua lendo o arquivo gravado (`tests/test_ui_vagas.py`)

## Comments

Implementado na branch `integration/fontes-gratuitas-vagas`.
