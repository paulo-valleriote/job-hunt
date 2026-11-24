# 02: Contrato completo da API v1 do Rebase

Type: research
Status: resolved
Blocked by: none
Label: wayfinder:research (AFK)

## Question

O que o contrato público (`/api/v1/openapi.json`, `/api/v1/meta`, `/jobs/llms.txt`, `/jobs/api`) diz sobre os pontos abaixo? A pesquisa usa só fontes abertas, sem token.
- Schema completo da vaga na listagem e no detalhe: tipos, nulabilidade, o que `url` aponta em contraste com `apply_url`, e o formato de `location`, `seniority`, `skills` e `published_at`/`first_seen_at`.
- Se a listagem aceita filtro ou ordenação por data. Qual é a ordem padrão.
- Os códigos de erro (`error.code`) e quando aparece cada um (401, 403, 404, 422, 429).
- O vocabulário completo de `nivel`, `modelo` e dos slugs de `skill`, e quais casam com Go, TypeScript, Node.js e AWS.
- Se `GET /api/v1/agent/jobs` (listagem já com a descrição) é preferível a `jobs` + `jobs/{slug}` para o caso do `/busca`.

## Comments

- Pesquisa disparada em 2026-11-24 na branch `research/rebase-api-contrato` (achados em `.scratch/rebase-jobs/research/02-contrato-da-api.md` nessa branch; nunca será mergeada).

## Answer

Achados completos na branch `research/rebase-api-contrato`, em `.scratch/rebase-jobs/research/02-contrato-da-api.md`. Fonte: só o contrato público, sem token.
- **Acesso**: o catálogo exige token desde 2026-10-04. Só `/api/v1`, `/meta` e `openapi.json` são abertas.
- **Erros**: 401 `unauthorized` (token ausente ou revogado), 403 `forbidden` (falta o aceite de Novidades), 404 `not_found` (só em `jobs/{slug}`), 422 `invalid_params`, 429 `rate_limited` com `Retry-After`.
- **Data**: a listagem não filtra nem ordena por data. A ordem padrão é `published_at` decrescente; com `q`, os matches no título vêm antes e depois a data. O corte por janela tem de ser local.
- **Links**: `url` é a página da vaga no catálogo do Rebase. `apply_url` é a candidatura no ATS e pode ser nulo. O contrato não exige atribuição.
- **Requisitos**: vêm de `skills_principais`, não de `skills`.
- **Busca com `q`**: quando há poucos resultados, `meta.busca.dica` sugere trocar `onde=titulo` por `onde=tudo`.
- **`GET /api/v1/agent/jobs`**: traz a listagem com a descrição em 1 requisição, contra 1+N de `jobs` + `jobs/{slug}`. É preferível se o script precisar da descrição.
- **Vocabulário**:
  - `nivel`: junior | pleno | senior | staff | lideranca (usar o slug sem acento).
  - `modelo`: clt | pj | eor | nao-informado.
  - São 66 skills. Go = `go`, TypeScript = `typescript`, Node.js = `nodejs`, AWS = `aws`.
- **Lacunas**: a semântica de `first_seen_at`, o formato de `location`, o tamanho máximo de `agent/jobs` e os termos de atribuição. A amostra autenticada pode esclarecer.
