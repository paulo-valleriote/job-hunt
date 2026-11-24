# 14: LinkedIn pula vagas que o Rebase já trouxe

**What to build:** na rodada, a coleta do Rebase roda antes do LinkedIn. O `/busca` não abre no navegador as vagas do LinkedIn que o Rebase já trouxe (mesma empresa e mesmo título, normalizados), e o fechamento da rodada diz quantas foram puladas. Na duplicata que ainda passar, fica a vaga do Rebase e o LinkedIn aparece como fonte secundária, pela dedupe existente.

- `busca.py candidatos` ganha `--coletadas <json>`. Uma vaga da listagem do LinkedIn com a mesma empresa e título de uma vaga do Rebase sai antes da verificação, com o motivo "já veio do Rebase" no stderr.
- O `.claude/commands/busca.md` roda o Rebase antes do LinkedIn, passa `--coletadas` ao `candidatos` no passo 6 e informa no fechamento quantos cortes "já veio do Rebase" houve.

Fonte: `.scratch/rebase-jobs/spec.md`, histórias 23–28 e seção "Mudanças no `busca.py`", item `candidatos`.

**Blocked by:** 10 (Coleta do Catálogo Rebase)

**Status:** resolved

- [x] `candidatos --coletadas` remove as vagas do LinkedIn que casam por empresa e título com uma vaga do Rebase, e avisa "já veio do Rebase" no stderr
- [x] Sem `--coletadas`, o `candidatos` se comporta como hoje
- [x] Na duplicata entre Rebase e LinkedIn em `processar()`, fica a do Rebase e o LinkedIn vira fonte secundária
- [x] O `busca.md` coleta o Rebase antes do LinkedIn, passa `--coletadas` no passo 6 e relata os cortes no fechamento
- [x] Há testes novos do `candidatos --coletadas`, pela CLI por subprocess
