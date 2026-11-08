# 14: UI: telas Currículos e Tracker

**What to build:** O usuário gera e consulta currículos e acompanha as candidaturas pela interface local: vê o PDF, a nota e o relatório de cobertura, e edita o tracker como uma tabela.

**Blocked by:** 13 (UI base + tela Vagas), 09 (Avaliador + ciclo de revisão), 10 (Anti-invenção), 11 (`/enviei`)

**Status:** ready-for-agent

- [ ] Tela **Currículos**: lista os currículos gerados, mostra PDF, nota, `coverage_review.md` e `rating_report.md`, e tem botão de gerar (chama o mesmo `/curriculo` via `claude -p`)
- [ ] Tela **Tracker**: tabela editável do `private/tracker.csv`, que continua sendo a fonte de verdade e abrindo no Excel
- [ ] Nenhuma lógica duplicada: a UI só chama os comandos existentes
- [ ] Tudo o que a UI faz também funciona pelos comandos
- [ ] Segue só em `localhost`
