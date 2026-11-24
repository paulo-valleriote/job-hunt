# 02: Contrato da API v1 do Rebase (pesquisa)

Data da coleta: 2026-11-24. Fontes abertas, sem token, sem login. Cinco requisições no total, com User-Agent genérico, a 1 s de intervalo.

Fontes e abreviações usadas nas citações:
- **OAS** = `https://rebasedev.com.br/api/v1/openapi.json` (OpenAPI 3.0, 7.526 linhas ao formatar). Caminhos citados como `components.schemas.X.properties.Y` ou `paths./api/v1/jobs.get.parameters[name=…]`.
- **META** = `https://rebasedev.com.br/api/v1/meta` (sem token).
- **IDX** = `https://rebasedev.com.br/api/v1` (sem token).
- **LLMS** = `https://rebasedev.com.br/jobs/llms.txt`, citado por seção (ex.: "LLMS, § As rotas").
- **DOC** = `https://rebasedev.com.br/jobs/api` (visualizador HTML), citado por seção.

Ressalva geral: o OAS diz que é gerado do código que serve a API (`info.description`), então é a fonte mais precisa. Em LLMS e DOC há divergências menores (listadas no fim). Nada aqui foi testado com token; respostas reais de 200 com dados de conta não foram vistas.

---

## 0. O que muda para o `/busca` (resumo para os tickets 04, 05 e 07)

1. **O catálogo exige token pessoal desde 2026-10-04.** `components`/`info.description`: "O catálogo pede token pessoal (desde 2026-10-04)". `GET /api/v1/jobs`, `/jobs/{slug}`, `/agent/jobs` e `/companies` têm `security: [{token: []}]` (OAS, `paths./api/v1/jobs.get.security`). Abertas sem token: `/api/v1`, `/api/v1/meta` e `/api/v1/openapi.json` (OAS, `security: []`; IDX `autenticacao.abertas_sem_token`). Impacto: o gate de token (ticket 07) é obrigatório para a fonte Rebase; sem token, só o `meta` é útil, e ele não traz vagas.
2. **Token precisa de conta com aceite de Novidades.** Sem o aceite, o token responde 403 `forbidden` (OAS, `info.description`, "**Acesso.**"; LLMS, "## Acesso: conta e aceite das Novidades"). Gerar outro token não resolve (OAS, `paths./api/v1/jobs.get.responses.403`).
3. **Token revogado ou inválido é 401 `unauthorized`** com `WWW-Authenticate: Bearer` (OAS, `…responses.401`). Token do OAuth do MCP é 401 aqui (OAS, `info.description`).
4. **`link` do `/busca`:** o campo `url` é a página do catálogo no Rebase, e `apply_url` é o link de candidatura no ATS (ver seção 1). Para o campo `link` do registro, a decisão do ticket 05 depende de qual dos dois a Rebase pede para citar. Ver lacuna L3.
5. **`published_at` é a chave de ordenação padrão.** A listagem ordena por data de publicação, da mais nova para a mais antiga (OAS, `…get.parameters[name=q].description`). `first_seen_at` não aparece em nenhuma regra de ordenação (ver seção 2).
6. **`skills_principais` é o campo que o filtro `skill` lê.** `skills` é a lista completa citada; `skills_principais` é o que a vaga pede (OAS, `components.schemas.Job.properties.skills_principais.description`). Para o ticket 05 (`requisitos`), a escolha natural é `skills_principais`, mas isso é decisão de produto, não contrato.
7. **Ordem da busca com `q`:** título primeiro, depois descrição; data dentro de cada grupo. Com `onde=titulo` só o título. Com `onde=tudo` título e descrição numa lista só, por data (OAS, `…parameters[name=onde]`). Se o `total` vier pequeno, a API sugere o outro modo em `meta.busca.dica` (OAS, `components.schemas.Meta.properties.busca`). Isso importa para o ticket 04 (cargo com `onde=titulo` pode perder vaga cuja descrição fala do cargo).
8. **Pagina e limita:** `por_pagina` padrão 20, máximo 50; acima de 50 a API responde 422, não trunca (OAS, `…parameters[name=por_pagina]`). `pagina` vai até 500 (OAS, `…parameters[name=pagina]`).
9. **Limite:** 60 chamadas por minuto por conta (com token) ou por IP (sem token). Respostas com sucesso trazem `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`; o 429 traz também `Retry-After` (OAS, `info.description`, "**O limite é de 60 chamadas por minuto, por conta**"; `…responses.429`).
10. **`agent/jobs` vs `jobs` + `jobs/{slug}`:** ver pergunta 5. Recomendação: para a rodada diária, uma chamada de `agent/jobs` com `por_pagina=50` economiza requisições; o custo é payload maior.

---

## 1. Schema da vaga (pergunta 1)

Há três variantes de vaga na API. Todas trazem os mesmos campos de base; a diferença é só o que o listagem omite.

- **Listagem (`GET /api/v1/jobs`):** `components.schemas.JobNaBusca`. Não traz `description` nem `description_md`. Traz `oculta`. Com `minhas_skills=true` traz também `skills_em_comum`.
- **Listagem com texto (`GET /api/v1/agent/jobs`):** `components.schemas.JobDetailNaBusca`. Traz `description` (e `description_md` com `formato=markdown`), `closed_at`, `tambem_publicada`, `oculta`.
- **Detalhe (`GET /api/v1/jobs/{slug}`):** `components.schemas.JobDetail` dentro de `JobDetailResponse` (envelope `{data: …}`). Não traz `oculta` (o schema `JobDetail` não tem essa propriedade; ver lacuna L7).

Campos com tipo, nulabilidade e fonte (todos em `components.schemas.Job`, salvo indicação):

| Campo | Tipo (OAS) | Nulo? | Notas e citação |
|---|---|---|---|
| `slug` | string | não | Endereço da vaga; a API endereça por slug, nunca por id interno (`paths./api/v1/jobs/{slug}.get.description`). |
| `title` | string | não | Título do anúncio. |
| `company` | object `{name, slug}` | **sim** (`nullable: true`) | `company.slug` é o valor que o filtro `empresa` aceita. |
| `location` | string | **sim** | Texto livre; o exemplo é `"Remote (Worldwide)"`. Formato não documentado além do exemplo (lacuna L5). |
| `hires_in_brazil` | enum `unknown`/`yes`/`no` | não | "Na prática é sempre `yes`; as outras só aparecem em `eu/vagas`" (`…hires_in_brazil.description`). |
| `decidido_pela_curadoria` | boolean | não | `true` quando o `yes` é decisão manual da curadoria, sem prova no texto (`…decidido_pela_curadoria.description`). |
| `remote` | boolean | **sim** | Campo cru do ATS; nulo é o comum e "não quer dizer que a vaga não é remota" (`…remote.description`). |
| `work_mode` | enum `remote`/`hybrid`/`onsite`/null | **sim** | Campo cru do ATS, normalizado; mesma ressalva de `remote` (`…work_mode.description`). |
| `remoto_comprovado` | boolean | não | "Na prática é sempre `true`" para vagas devolvidas pela API (`…remoto_comprovado.description`). Este é o campo que prova remoto. |
| `seniority` | enum `júnior`/`pleno`/`sênior`/`staff`/`liderança`/null | **sim** | Rótulo com acento (ver pergunta 4). Nulo quando o título e o anúncio não dizem; "o catálogo não chuta" (`…seniority.description`). |
| `skills` | array de string | não | Lista completa de skills citadas. Itens sem enum no schema; os slugs vêm do dicionário de `meta.skills` (ver pergunta 4). |
| `skills_no_titulo` | array (itens sem tipo, `items: {}`) | não | Skills citadas no título. Tipo dos itens não documentado (lacuna L6). |
| `skills_principais` | array de string | não | O que a vaga pede; lido pelo filtro `skill`. Inclui o "ou" de elegibilidade (`Python, Go, or Rust` → as três). Vaga não reprocessada repete `skills` (`…skills_principais.description`). |
| `skills_diferenciais` | array de string | não | "Nice to have" ou "bonus"; vazio quando não há ou não reprocessada (`…skills_diferenciais.description`). |
| `hiring_models` | array, itens `pj`/`eor`/`clt` | não (pode ser vazio) | Modelo no Brasil que o anúncio afirma ou, na falta, o da empresa. Vazio = `nao-informado` (`…hiring_models.description`). |
| `salary` | string | **sim** | Texto de exibição, ex.: `"US$ 90K – US$ 120K por ano"`. |
| `salary_min`, `salary_max` | integer | **sim** | Valores numéricos. |
| `salary_currency` | string | **sim** | Ex.: `"USD"`. Lista de moedas não documentada. |
| `salary_interval` | enum `YEAR`/`MONTH`/`HOUR`/null | **sim** | Período de `salary_min`/`salary_max` (`…salary_interval.description`). |
| `published_at` | string, `format: date-time` | **sim** | Exemplo `"2026-09-24T15:00:00.000+00:00"`. Chave de ordenação (ver pergunta 2). Descrição própria ausente; significado vem da ordenação em `paths./api/v1/jobs.get.parameters[name=q]`. |
| `first_seen_at` | string, `format: date-time` | **sim** | Exemplo `"2026-09-25T09:00:00.000+00:00"`. **Sem descrição no schema.** Não documentado o que exatamente marca (lacuna L2). |
| `apply_url` | string (sem `format`) | não (tipo string, sem `nullable`) | **Sem descrição no schema.** Exemplo: `https://boards.greenhouse.io/railway/jobs/4210561007`, ou seja, o link de candidatura no ATS. Não documentado se pode vir vazio. |
| `url` | string, `format: uri` | não | Descrição: "A página da vaga no catálogo, em URL absoluta. É o link pra repassar a uma pessoa ou citar como fonte." Exemplo: `https://rebasedev.com.br/jobs/senior-backend-engineer-4210561007`. |

Campos extras do detalhe (`JobDetail`):
- `description` (string, não nula): texto puro do anúncio. Exemplo do OAS: "We are hiring a Senior Backend Engineer…".
- `description_md` (string, **nula**): só com `formato=markdown`; nulo quando o ATS só entregou texto puro (`…description_md.description`).
- `closed_at` (date-time, nulo enquanto aberta): "Quando a vaga saiu do ATS" (`…closed_at.description`).
- `tambem_publicada` (array de `{local, url_de_candidatura}`): outras publicações abertas do mesmo anúncio. `local` pode ser nulo; `url_de_candidatura` é uri (`…tambem_publicada.description`). Útil para o ticket 05 porque o `apply_url` pode não ser a única candidatura.

Campo extra só da listagem:
- `oculta` (boolean): `true` quando a conta dona do token ocultou a vaga (`JobNaBusca.properties.oculta`).
- `skills_em_comum` (integer, ≥ 0): só com `minhas_skills=true` (`JobNaBusca.properties.skills_em_comum`).

**Resposta da listagem:** `{ "data": [JobNaBusca…], "meta": Meta }` (`components.schemas.JobListResponse`). **Resposta do detalhe:** `{ "data": JobDetail }` (`components.schemas.JobDetailResponse`). Envelope fixo, conforme `info.description` ("O envelope é fixo e não muda").

**Meta da listagem (`components.schemas.Meta`):** obrigatórios `total`, `pagina`, `paginas`, `por_pagina`. Opcionais: `previa` (boolean; sempre `false` hoje), `mostrando`, `busca` (com `q`), `ignored_params` (parâmetros desconhecidos, com `did_you_mean`). Confira `ignored_params`: é a forma de descobrir que um filtro foi ignorado (`info.description`; LLMS, "## Como se comportar aqui").

---

## 2. Filtro e ordenação por data (pergunta 2)

- **Filtro por data:** **não existe** nos parâmetros de `GET /api/v1/jobs` nem de `GET /api/v1/agent/jobs` (lista completa em `paths./api/v1/jobs.get.parameters`: `q`, `titulo`, `onde`, `esconder_ocultas`, `minhas_skills`, `empresa`, `skill`, `skills_modo`, `nivel`, `modelo`, `pagina`, `por_pagina`; `agent/jobs` soma `formato`). Não há `publicado_desde`, `since`, `desde` ou similar. Um parâmetro desconhecido volta em `meta.ignored_params`, não dá erro (OAS, `…get.description`). Logo, filtrar por data no servidor é **não documentado** / não suportado. Para a rodada diária, a filtragem por data tem de ser local (lacuna L1).
- **Ordenação por parâmetro:** **não existe** parâmetro `order`/`sort`. A ordem é fixa.
- **Ordem padrão:**
  - Sem `q`: "é só a data" (`…parameters[name=q].description`), ou seja, `published_at` decrescente (mais nova primeiro). O schema diz "da data de publicação (da mais nova pra mais antiga)".
  - Com `q` e `onde` ausente: vagas que casam no título primeiro, depois as que citam só na descrição; data decrescente dentro de cada grupo.
  - Com `skill`: vagas com a skill no título primeiro; depois as que só citam no texto; data dentro de cada grupo (`…parameters[name=skill].description`).
  - Com `minhas_skills=true`: a ordem vira "match" (mais skills em comum primeiro), e a data só no fim (`…parameters[name=minhas_skills].description`).
- **Desempate da data:** o schema não diz se `published_at` nulo cai no fim ou no começo (lacuna L2).

---

## 3. Códigos de erro (pergunta 3)

Envelope de erro: `{ "error": { "code": "…", "message": "…" } }` (`components.schemas.Error`). O campo `code` é o contrato; `message` pode mudar de redação (`info.description`, "**O envelope é fixo**…").

Valores do enum `components.schemas.Error.properties.error.properties.code`: `not_found`, `conflict`, `in_catalog`, `invalid_params`, `rate_limited`, `unauthorized`, `forbidden`, `bad_request`, `method_not_allowed`, `unsupported_media_type`, `server_error`, `cv_ilegivel`.

Por status, nas rotas de leitura do catálogo (`GET /api/v1/jobs`, `/jobs/{slug}`, `/agent/jobs`, `/companies`):

| Status | `code` | Quando (OAS) |
|---|---|---|
| 401 | `unauthorized` | Sem token, token inválido ou revogado. Traz `WWW-Authenticate: Bearer`, e com token inválido `error="invalid_token"` (`…responses.401`). |
| 403 | `forbidden` | Token válido, mas a conta não tem acesso ao catálogo pela API (ex.: não aceitou Novidades). "Gerar outro token não resolve" (`…responses.403`). |
| 404 | `not_found` | Só em `GET /api/v1/jobs/{slug}`: a vaga não está no catálogo, mesmo que a página exista no site (`…jobs/{slug}.responses.404`; `…get.description`). |
| 422 | `invalid_params` | Valor fora do teto (`por_pagina` > 50, `pagina` > 500), fracionário em `pagina`/`por_pagina`, skill, nível ou empresa inexistente, busca com menos de 2 caracteres, booleano inválido, `onde` fora de `titulo`/`tudo`, `formato` fora de `texto`/`markdown`, caractere nulo. Nas escritas: etapa desconhecida, skill fora do dicionário, campo desconhecido no corpo. `empresa` com slug inexistente responde 422, nunca lista vazia (`…parameters[name=empresa].description`). |
| 422 | `cv_ilegivel` | Só nas rotas `.../cv`: PDF sem texto legível. Não é das rotas de catálogo. |
| 429 | `rate_limited` | Mais de 60 chamadas no minuto. Espera `Retry-After` (segundos). Ver seção 0, item 9 (`…responses.429`). |

Outros códigos do enum e onde aparecem (escritas `eu/*`): `conflict` (409, ex.: apagar a mudança de etapa de uma vaga; `…eu/vagas/{slug}/historico/{evento}.delete.responses`), `in_catalog` (não identificado nas rotas lidas; não documentado onde se aplica), `bad_request`, `method_not_allowed` (405 com `Allow`), `unsupported_media_type`, `server_error`. Para o `/busca`, os que importam são 401, 403, 404, 422 e 429.

Observação: o `/busca` só lê o catálogo. As rotas de escrita (`eu/*`) não são necessárias para o fluxo de busca.

---

## 4. Vocabulário de `nivel`, `modelo` e `skill` (pergunta 4)

### `nivel` (parâmetro e `seniority`)

- Slugs aceitos (`…parameters[name=nivel].schema.items.enum`): `junior`, `pleno`, `senior`, `staff`, `lideranca`. Máximo 5 valores repetidos. Entre níveis vale **qualquer um** (OAS, `…nivel.description`).
- Rótulos de `seniority` e `meta.niveis[].label` (OAS, `components.schemas.Job.properties.seniority`; `MetaResponse…niveis`): `júnior`, `pleno`, `sênior`, `staff`, `liderança`.
- Contagem no snapshot (`meta.data.niveis`, 2026-11-24): junior 9; pleno 110; senior 252; staff 81; lideranca 70.
- Regra do nível: o que o título anuncia; se o título não diz, `pleno` quando o anúncio pede de 2 a 4 anos; `lideranca` cobre Manager, Head, Director, Lead, CTO (`…nivel.description`).
- Parâmetro aceita slug ou rótulo, com ou sem acento (`info.description`, "**Parâmetro vazio é parâmetro ausente**… `nivel` aceita o slug e o rótulo"). Isso contradiz a descrição do parâmetro, que fala de "slug sem acento". Usar sempre o slug sem acento é a escolha segura.

### `modelo`

- Slugs (`…parameters[name=modelo].schema.items.enum`): `clt` (CLT, pago em reais), `pj` (PJ ou contractor), `eor` (employer of record), `nao-informado`. Máximo 4 valores. Qualquer um dos valores vale (OAS, `…modelo.description`).
- Rótulos (`meta.data.modelos[].label`): `CLT (em reais)`, `PJ / contractor`, `EOR`, `Não informado`.
- Contagem no snapshot: clt 54; pj 97; eor 3; nao-informado 517. Uma vaga com PJ e EOR conta nos dois (`MetaResponse…modelos.description`).
- `nao-informado` quer dizer sem modelo nenhum, nem da vaga nem da empresa. Não é "nenhum" (LLMS, "Como se comportar aqui").

### `skill` (66 slugs no filtro)

Lista do enum (`…parameters[name=skill].schema.items.enum`, 66 valores), com contagem de `meta.data.skills` no snapshot:

- Casam com as quatro pedidas:
  - **Go**: slug `go`, label `Go`, categoria `linguagens`, total 119.
  - **TypeScript**: slug `typescript`, label `TypeScript`, categoria `linguagens`, total 202.
  - **Node.js**: slug `nodejs`, label `Node.js`, categoria `back-end`, total 102. Não existe `node` nem `node.js`. O `javascript` (total 182) é outra skill.
  - **AWS**: slug `aws`, label `AWS`, categoria `cloud-infra`, total 221.
- Demais slugs, com total (mesma fonte): python 268, ci-cd 197, javascript 182, sql 160, observability 158, react 156, postgres 152, testing 142, llm 142, ai-assisted-dev 133, data-engineering 131, docker 117, devops 106, azure 100, kubernetes 97, rest-api 94, distributed-systems 91, gcp 86, terraform 84, system-design 83, java 68, csharp 64, microservices 60, linux 56, mysql 53, graphql 47, kafka 47, html-css 46, rust 42, machine-learning 42, redis 39, cpp 31, nextjs 29, react-native 28, embedded 27, security 27, bash 27, ruby 24, mongodb 23, salesforce 23, kotlin 22, serverless 22, c 22, sre 22, php 20, elasticsearch 19, android 19, ios 19, angular 18, swift 16, vue 15, grpc 14, figma 14, tailwind 13, blockchain 7, scala 6, flutter 5, elixir 4, wordpress 3, devrel 3, unity 2, svelte 1.
- Categorias (`meta.data.categorias`): linguagens, front-mobile, back-end, ia-dados, cloud-infra, bancos, praticas, outros.
- Regras (`…parameters[name=skill].description`): até 10 valores; o filtro lê `skills_principais`, não toda skill citada; `ou` por padrão, `e` com `skills_modo=e`. Valor fora da lista responde 422, nunca lista vazia.
- **Atenção:** `skills_principais` (filtro) ≠ `skills` (lista completa). Uma vaga com `nodejs` em `skills_diferenciais` não casa `skill=nodejs`.

### Resumo de `meta`

`GET /api/v1/meta` (aberta, sem token) devolve no snapshot 2026-11-24: 671 vagas, 196 empresas (`meta.data.catalogo`). Limites: `por_pagina_max` 50, `por_pagina_padrao` 20 (`meta.data.limites`). Os totais mudam diariamente (LLMS, "## O recorte").

---

## 5. `GET /api/v1/agent/jobs` vs `jobs` + `jobs/{slug}` (pergunta 5)

Fatos do contrato:
- `agent/jobs` é a listagem com o texto de cada anúncio. Mesmos filtros de `jobs` (`paths./api/v1/agent/jobs.get.parameters`, incluindo `formato`). Descrição: "ler 20 vagas custa 1 request aqui e 21 na listagem normal. A resposta é grande por natureza, então gasta o limite da conta mais rápido." (`paths./api/v1/agent/jobs.get.description`).
- Com `formato=markdown` a resposta "quase dobra" (mesma descrição).
- `jobs/{slug}` devolve uma vaga por request, com o texto (`paths./api/v1/jobs/{slug}.get`).

Recomendação para o `/busca` (script diário):
- **Preferir `agent/jobs`** quando a rodada precisa de `description` para triagem ou para decidir por texto. Economiza requisições: 1 chamada em vez de 1 + N.
- Usar `jobs` (sem texto) quando a rodada só precisa de metadados e o texto só é lido para as vagas novas. Nesse caso, `jobs` + `jobs/{slug}` só para as novas.
- Usar `por_pagina=50` em qualquer caso, para reduzir o número de páginas.
- Limite: a 60/min, `agent/jobs` a 50 por página com `description` consome pouco em calls, mas o payload é grande. Não há teto de bytes documentado (lacuna L8).
- Não é possível concluir pelo contrato que `agent/jobs` é "sempre preferível": a diferença de custo é de requisições e de tamanho de resposta. Se o script só lê título e empresa para descartar a maioria, `jobs` é mais leve.

---

## 6. Lacunas e divergências

Lacunas (não documentado no contrato):
- **L1.** Filtro por data de publicação ou de primeira vista: não existe no contrato (seção 2). Filtragem local por `published_at`/`first_seen_at`.
- **L2.** Significado de `first_seen_at` (sem descrição) e tratamento de `published_at` nulo na ordenação.
- **L3.** Qual link o Rebase quer citado como fonte no registro do `/busca`. O contrato diz que `url` serve "pra repassar a uma pessoa ou citar como fonte" (`components.schemas.Job.properties.url.description`), mas `apply_url` não tem descrição. Os termos de uso não foram lidos: não estão nas fontes permitidas. **Atribuição obrigatória: não documentado**; os termos ficam em `https://rebasedev.com.br/jobs/como-funciona` (não consultado, fora das fontes da pesquisa) ou nos termos linkados no rodapé (LLMS, "Termos"). Não está no contrato.
- **L4.** Termos de uso e uso comercial/scraping: não documentado aqui.
- **L5.** Formato de `location` (texto livre; sem enum nem padrão além do exemplo).
- **L6.** Tipo dos itens de `skills_no_titulo` (`items: {}`). Valores possíveis não documentados.
- **L7.** O schema `JobDetail` não traz `oculta`, mas a descrição de `JobDetailNaBusca` traz. Não se sabe se o detalhe omite o campo de propósito.
- **L8.** Tamanho máximo de resposta de `agent/jobs` e limite de bytes: não documentado.
- **L9.** Se `apply_url` pode vir vazio ou nulo: o schema declara `type: string` sem `nullable`.
- **L10.** Comportamento de `in_catalog` (código de erro): aparece no enum, sem rota de leitura citada onde ocorre.
- **L11.** Se há versão de contrato além de `v1` e prazo de descontinuação. `info.description` diz "É o que evita um `/v2` por muito tempo" (regra de evolução), sem prazo.
- **L12.** Comportamento do token de OAuth e de token pessoal com as mesmas rotas de leitura: está descrito, mas não testado.
- **L13.** Horário da varredura e frescor dos dados: LLMS diz 6h e 18h (horário de Brasília), mas não há SLA.

Divergências entre fontes:
- **D1.** `nivel` aceita slug e rótulo com acento segundo `info.description`, mas a descrição do parâmetro diz "slug sem acento". Usar o slug.
- **D2.** DOC (`/jobs/api`) cita `GET /api/v1/jobs: busca (q, titulo, empresa, skill, nivel)`, sem `onde`, `modelo`, `minhas_skills` etc. O OAS é a fonte completa.
- **D3.** LLMS, "Autorização", diz que a API e o MCP aceitam o mesmo token pessoal; OAS, `info.description`, diz que o token do OAuth vale só no MCP e é 401 na API. Não há conflito sobre o token pessoal: para o `/busca`, usar token pessoal.
- **D4.** LLMS cita `titulo=true` como sinônimo de `onde=titulo`, consistente com o OAS (`…parameters[name=titulo]`). Sem divergência real; o OAS diz "Prefira `onde`".
- **D5.** LLMS, "## As rotas", diz que a listagem sem `q` tem "só a data"; consistente com o OAS.

---

## 7. Fontes e requisições

| # | URL | Resultado |
|---|---|---|
| 1 | `https://rebasedev.com.br/api/v1/openapi.json` | 200, 186.310 bytes, lido por inteiro (formatado em `openapi.pretty.json`) |
| 2 | `https://rebasedev.com.br/api/v1/meta` | 200, 5.971 bytes |
| 3 | `https://rebasedev.com.br/api/v1` | 200, 2.412 bytes |
| 4 | `https://rebasedev.com.br/jobs/llms.txt` | 200, 11.640 bytes |
| 5 | `https://rebasedev.com.br/jobs/api` | 200, 35.365 bytes (HTML, texto extraído) |

Os arquivos baixados ficaram em `/tmp/claude-1000/-home-pmv-programming-job-hunt/9999a83f-59a4-4c3e-9a8a-030ddf93a2cd/scratchpad/rebase-api/` (fora do repositório). Não foi feita nenhuma requisição com token, nem a rotas de escrita, nem a `/api/jobs` (que já dá 404).
