# 10: Coleta do Catálogo Rebase no `busca.py coletar` (caminho feliz)

**What to build:** o passo de coleta por script do `/busca` passa a ler só o **Catálogo Rebase** e grava as vagas como registros de vaga com `fonte: rebase`. Esse passo continua devolvendo `{vagas, falhas}`, no mesmo formato de hoje.

- Um módulo novo, o adaptador do Rebase, é o único que fala com a API (`https://rebasedev.com.br/api/v1`).
- Interface pública: uma função de coleta `(config, token, fetch, sleep) → {vagas, falhas}`, com `fetch` e `sleep` injetáveis, seguindo o padrão da coleta antiga.
- Token: lido da variável `TOKEN` de `private/rebase.env` (não `REBASE_TOKEN`).
- Tradução da stack: o `stack_desejada` do `busca.yaml` vira slugs, com normalização (sem caixa, sem acento, sem pontuação) e uma tabela pequena de apelidos (golang→go, node.js→nodejs). Slugs confirmados: `go`, `typescript`, `nodejs`, `aws`.
- Consulta: `GET /jobs` com `Authorization: Bearer`, `por_pagina=50` e um `skill` por slug. Não envia `q`, `nivel`, `modelo` nem `minhas_skills`, e `cargos_alvo` não vai para o Rebase. A leitura segue até 10 páginas ou até a última, sem parada antecipada.
- Tradução de cada vaga para registro de vaga: segue a tabela da spec (`link` = `apply_url`, `atribuicao` = `url`, `modalidade` remoto, `elegibilidade` brasil, `evidencia` citando o Rebase e a `location`, `data` de `first_seen_at`, `requisitos` de `skills_principais`, `trecho` com modelo e salário).
- Descartes, com motivo: vaga com `apply_url` nulo; nível `sênior`, `staff` ou `liderança` (acentuados), com o motivo `nível acima do alvo (<nível>)`. Vaga sem nível (`null`) fica.
- A janela "desde a última busca", os filtros de título e as empresas de `vagas_excluidas.md` valem para as vagas do Rebase.
- Na dedupe, o Rebase passa a ter prioridade 0 e o LinkedIn fica com prioridade 1. O teto de 50 e o rodízio não mudam.
- `http_get` e `motivo_da_falha` passam a morar no adaptador. O módulo antigo pode importá-las de lá até ser removido no ticket 15.
- O Guardrail 7 do `CLAUDE.md` ganha a nova redação da spec (senioridade e stack do `busca.yaml` podem ir em consultas externas; `minhas_skills` continua proibido). Isso precisa entrar antes de a primeira consulta mandar a stack para fora.

Fonte: `.scratch/rebase-jobs/spec.md`, seções "Consulta", "Tradução vaga do Rebase → registro de vaga" e "Instruções e regras".

**Blocked by:** None (can start immediately)

**Status:** resolved

- [x] `busca.py coletar` chama o adaptador do Rebase e grava `{vagas, falhas}` com vagas `fonte: rebase`
- [x] O token é lido da linha `TOKEN=` de `private/rebase.env`
- [x] A stack é traduzida em slugs por normalização e apelidos (ex.: "Golang" → `go`, "Node.js" → `nodejs`)
- [x] A consulta leva o header Bearer, `por_pagina=50` e um `skill` repetido por slug, sem `q`, `nivel`, `modelo` nem `minhas_skills`
- [x] A paginação para na última página ou na 10ª, o que vier antes
- [x] Cada campo do registro segue a tabela da spec, incluindo `requisitos` vazio quando não há skills, `trecho` com e sem modelo e salário, e `data` vinda de `first_seen_at`
- [x] Vagas com `apply_url` nulo e de nível `sênior`, `staff` ou `liderança` são descartadas com motivo; vagas sem nível ficam
- [x] A janela `desde`, os filtros de título e `vagas_excluidas.md` valem para as vagas do Rebase
- [x] O Rebase tem prioridade 0 na dedupe; os testes de dedupe e rodízio que usavam greenhouse, lever ou himalayas são reescritos com `fonte="rebase"`, mantendo os comportamentos
- [x] `http_get` e `motivo_da_falha` moram no adaptador
- [x] O Guardrail 7 do `CLAUDE.md` tem a nova redação
- [x] O teste do adaptador usa só `fetch` e `sleep` falsos, sem rede, sem token real e sem nada de `private/`
- [x] `make test-busca` passa
