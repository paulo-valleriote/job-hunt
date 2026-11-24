# 04: Como o busca.yaml vira consulta ao Rebase

Type: grilling
Status: resolved
Blocked by: 02, 03
Label: wayfinder:grilling (HITL)

## Question

Quais chamadas o script faz a partir do `busca.yaml`? Pontos a decidir:
- Uma chamada por cargo (`q=<cargo>&onde=titulo`) ou uma chamada ampla (`nivel` + `skill`) com o título filtrado localmente por `titulos_incluidos`/`titulos_excluidos`?
- `skills_modo` qualquer ou todas.
- Os níveis enviados, considerando que a senioridade aceita mid-senior com match alto de stack.
- Quantas páginas ler e qual teto de requisições por rodada, dentro do limite de 60 por minuto.
- Os campos novos que o `busca.yaml` precisa, se houver, com um exemplo em `busca.example.yaml`.

## Answer

Decidido com o usuário em 2026-11-24. A base são os números do ticket "Amostra real autenticada do catálogo".

1. **Uma consulta ampla, por stack**: `GET /api/v1/jobs?skill=<slug>&skill=<slug>…`, com `skills_modo` no padrão (vale qualquer uma) e `por_pagina=50`. A consulta não leva `q`, então os `cargos_alvo` não vão para o Rebase; eles continuam servindo só para o LinkedIn. O escopo por título fica no filtro local que já existe (`titulos_incluidos`/`titulos_excluidos`).
2. **O nível é filtrado localmente, não pela API**: a consulta não manda `nivel`, porque isso derrubaria as vagas com `seniority: null`. O script lê `seniority` e mantém `júnior`, `pleno` e `null`. Descarta `staff` e `liderança` com o motivo "nível acima do alvo (<nível>)".
3. **Sênior do Rebase é descartado na busca**, com o motivo "nível acima do alvo (sênior)". O custo, aceito, é perder alguma vaga sênior com stack muito aderente. No LinkedIn, que não traz o nível como campo, a regra continua só pelo título.
4. **Paginação**: a API devolve as vagas por `published_at`, da mais nova para a mais antiga. Com o corte da janela por `published_at`, a leitura para na primeira vaga anterior à janela. Em qualquer caso, o teto é de **10 páginas** (500 vagas, 10 requisições). Se o ticket "Vaga do Rebase → registro de vaga do /busca" escolher `first_seen_at` para a data, a parada antecipada deixa de valer e a leitura vai até o teto.
5. **A busca usa `/jobs`, não `/agent/jobs`**, e não lê a descrição das vagas. Usar a descrição no `/triagem` continua em "Not yet specified".
6. **A stack sai do `stack_desejada`**, sem campo novo no `busca.yaml`. O script traduz os nomes por normalização (sem caixa, sem acento, sem pontuação) com uma tabela pequena de apelidos (ex.: golang→go, node.js→nodejs). O resultado é conferido contra a lista de skills do `/api/v1/meta`. Uma stack que não casar faz o `make check-config` falhar com mensagem clara. O `minhas_skills` continua proibido (Guardrail 7 ampliado).
