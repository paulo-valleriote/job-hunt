# 09: Avaliador separado + ciclo de revisão

**What to build:** Todo currículo gerado por `/curriculo` passa por um avaliador independente de quem escreveu, é revisado automaticamente enquanto a nota melhorar, e o usuário recebe a melhor versão com o histórico de notas.

**Blocked by:** 08 (`/curriculo` básico)

**Status:** done (pendente validação humana com vaga real)

- [x] Subagente avaliador, separado do que escreve, devolve nota de 1 a 10, pontos fortes, lacunas e palavras-chave
- [x] Revisão pelo prompt `04b-ajustar-curriculo` até a nota 8.5, no máximo 3 revisões
- [x] Para quando uma revisão não melhora a nota
- [x] Entrega a versão de **melhor nota**, não necessariamente a última
- [x] `rating_report.md` mostra o histórico de notas, o motivo da parada e qual versão foi entregue
- [ ] Teste com vaga real mostra o ciclo funcionando de ponta a ponta
- [x] Se a cota da assinatura apertar, o teto de revisões é configurável (reduzir de 3 para 1)

**Nota:** compartilha o fluxo do `/curriculo` com o ticket 10; coordenar a ordem de merge se rodarem em paralelo.

## Notas da implementação
- Lógica em `scripts/avaliador.py` (`validar`, `decidir`, `finalizar`), testes em `tests/test_avaliador.py` (`make test-avaliador`). Versões em `versoes/vN/{resume.json,avaliacao.json}`; avaliador = subagente separado, orquestrado por `.claude/commands/curriculo.md` (passo 8b).
- Teto configurável: `--max-revisoes` ou `JOBHUNT_MAX_REVISOES`. Empate de nota: entrega a mais antiga.
- CLI do upstream conferida: `validar_json.py <json>` e `json_para_latex.py <json> <tex>` estavam corretas.
- Pendente humano: rodar `/curriculo` com uma vaga real (critério "teste com vaga real" segue `[ ]`) e conferir o subagente avaliador de fato separado.
