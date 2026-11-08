# 09: Avaliador separado + ciclo de revisão

**What to build:** Todo currículo gerado por `/curriculo` passa por um avaliador independente de quem escreveu, é revisado automaticamente enquanto a nota melhorar, e o usuário recebe a melhor versão com o histórico de notas.

**Blocked by:** 08 (`/curriculo` básico)

**Status:** ready-for-agent

- [ ] Subagente avaliador, separado do que escreve, devolve nota de 1 a 10, pontos fortes, lacunas e palavras-chave
- [ ] Revisão pelo prompt `04b-ajustar-curriculo` até a nota 8.5, no máximo 3 revisões
- [ ] Para quando uma revisão não melhora a nota
- [ ] Entrega a versão de **melhor nota**, não necessariamente a última
- [ ] `rating_report.md` mostra o histórico de notas, o motivo da parada e qual versão foi entregue
- [ ] Teste com vaga real mostra o ciclo funcionando de ponta a ponta
- [ ] Se a cota da assinatura apertar, o teto de revisões é configurável (reduzir de 3 para 1)

**Nota:** compartilha o fluxo do `/curriculo` com o ticket 10; coordenar a ordem de merge se rodarem em paralelo.
