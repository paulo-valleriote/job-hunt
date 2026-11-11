# 08: Fechamento do `/busca` por fonte e diagnóstico de falhas

**What to build:** o fechamento do `/busca` informa quantas vagas vieram de cada fonte e quantas foram descartadas, por motivo. Aponta também qual fonte falhou na rodada e qual token passou a dar 404, para o usuário revisar a lista. Continua sem classificar, ordenar por nota nem recomendar vagas.

**Blocked by:** 07, 03, 04

**Status:** resolved

- [ ] Fechamento lista vagas por fonte e descartes por motivo
- [ ] Fonte com falha e token 404 aparecem no fechamento
- [ ] Sem classificação, nota ou recomendação no fechamento
- [ ] Testes cobrem o relatório com fonte falha e token 404

## Comments

Implementado na branch `integration/fontes-gratuitas-vagas`.
