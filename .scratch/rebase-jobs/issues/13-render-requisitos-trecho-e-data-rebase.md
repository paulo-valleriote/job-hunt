# 13: Arquivo do dia: requisitos e trecho juntos, "entrou no Rebase em"

**What to build:** no arquivo do dia, a linha `- Trecho:` mostra os requisitos e o trecho juntos. Hoje ela mostra `requisitos or trecho`, o que esconde o salário quando há requisitos. Nas vagas com `fonte: rebase`, a linha `- Data:` diz "entrou no Rebase em <data>". As chaves `Data` e `Trecho` continuam as mesmas, porque o parser da `ui/` lê por chave.

Fonte: `.scratch/rebase-jobs/spec.md`, seção "Mudanças no `busca.py`", item `render`.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] Uma vaga com requisitos e trecho mostra os dois na linha `- Trecho:`
- [ ] Uma vaga só com requisitos, ou só com trecho, mostra o que tiver, sem separador sobrando
- [ ] `- Data:` diz "entrou no Rebase em" nas vagas `fonte: rebase` e fica como hoje nas outras
- [ ] Os testes da `ui/` (`make test-ui`) continuam passando sem mudança na `ui/`
- [ ] Há casos novos na classe `Render` dos testes do `busca`
