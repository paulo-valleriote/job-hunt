# 17: revisão do currículo com feedback do avaliador

**What to build:** na última execução real (`2026-11-09-alignerr-...`) a v1 tirou 8.4 e a revisão v2 caiu para 7.5. O passo 8b do `/curriculo` gera a v(N+1) sem a `avaliacao.json`, então a revisão é cega à nota e às palavras-chave. O upstream (`meu-emprego-novo`, CLI) passa o texto do avaliador ao editor; fazemos o mesmo, só com o que não empurra para invenção.

**Blocked by:** 09

**Status:** ready-for-human

- [x] `.claude/commands/curriculo.md` (passo 8b): o editor recebe, além dos anexos atuais, `pontos_fortes` e `palavras_chave` da `avaliacao.json` da versão atual; **nunca** `lacunas` nem sugestões de "como cobrir"
- [x] Instrução ao subagente avaliador (passo 8b-a): "só pontue o que está escrito no currículo e provado pelo `profile_truth.md`; requisito sem prova é lacuna e não sobe a nota"
- [x] `04b-ajustar-curriculo.md` é do upstream (`vendor/`, nunca modificado): a instrução extra vai no `curriculo.md`, não no prompt do upstream
- [x] Teste: `tests/test_avaliador.py` cobre que o ciclo continua parando em "não melhorou" e entregando a de melhor nota (comportamento atual, sem regressão)
- [ ] Validação humana: rodar `/curriculo` numa vaga e comparar as notas v1 → v2 com e sem o feedback

## Notas

- Não adotar a parte do upstream em que o avaliador sugere como cobrir lacuna; foi justamente isso que o 04b proíbe ("lacuna continua sendo lacuna").
- Guardrail 8 inalterado: avaliador separado, alvo 8.5, máx. 3 revisões, parar se não melhorar, entregar a melhor.
