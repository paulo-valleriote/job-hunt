# 03: Amostra real autenticada do catálogo

Type: task
Status: resolved
Blocked by: 01
Label: wayfinder:task (AFK)

## Question

Como é uma resposta real da API para os critérios do `busca.yaml`? Chamar `/api/v1/jobs` com combinações de `q`/`onde=titulo` (cargos), `nivel=junior,pleno` e `skill` (stack). Salvar as respostas em `private/rebase-amostra/`, nunca no git. No ticket, registrar só os fatos: o total por combinação, quantas vagas têm `seniority`, `salary` e `location` preenchidos, exemplos de valores de `location`, e se `apply_url` é sempre preenchido.

## Answer

Concluído em 2026-11-24. Foram 10 chamadas autenticadas, sem dado pessoal nos parâmetros. As respostas cruas estão em `private/rebase-amostra/*.json`, fora do git. O script da coleta é descartável e ficou no scratchpad da sessão. Os números contam só a 1ª página (até 50 vagas) de cada combinação. São 214 vagas distintas no total.

**Totais por combinação** (`por_pagina=50`; os multivalores vão como parâmetro repetido, ex.: `nivel=junior&nivel=pleno`, e nenhum caiu em `ignored_params`):
| Consulta | Total | Observação |
|---|---|---|
| `q=Backend Engineer&onde=titulo` | 51 | `dica`: 292 com `onde=tudo` |
| `q=Software Engineer&onde=titulo` | 131 | 426 com `onde=tudo` |
| `q=Forward Deployed Engineer&onde=titulo` | 19 | 57 com `onde=tudo` |
| `q=Golang Developer&onde=titulo` | **0** | `dica`: 27 citam o termo só na descrição |
| `nivel=junior,pleno` | 119 | |
| `skill=go,typescript,nodejs,aws` (qualquer) | 389 | |
| `nivel=junior,pleno` + as 4 skills | **65** | |
| `nivel=junior,pleno` + `skill=go` | 22 | |
| `nivel=junior,pleno` + `typescript`+`nodejs` com `skills_modo=e` | 12 | |
| `agent/jobs` com nível + 4 skills, `formato=markdown` | 65 | 1ª página com **540 KB** (contra 56 KB em `jobs`); `description_md` tem em média cerca de 4,7 mil caracteres |

**Preenchimento dos campos** (214 vagas):
- **Sempre preenchidos**: `apply_url`, `url`, `location`, `published_at` e `first_seen_at` (214 de 214).
- `hires_in_brazil`: sempre `"yes"`, como string.
- `skills_principais`: 205. `seniority`: 179. `remote`/`work_mode`: cerca de 148.
- `salary`: 40. `hiring_models` não vazio: 43 (30 pj, 12 clt, 1 eor).
- `remoto_comprovado`: `true` nas 50 vagas do `agent/jobs`.

**Valores e formatos:**
- `seniority` vem **com acento** na resposta: `pleno`, `sênior`, `júnior`, `staff`, `liderança` ou `null`. O filtro aceita o slug sem acento.
- O filtro `nivel` **exclui** as vagas com `seniority: null`. Na consulta por cargo "Backend Engineer", 11 de 50 eram `null`, e quase todo o resto era sênior ou staff.
- `location` é texto livre do ATS, por exemplo: `Brazil` (31), `Remote, Global` (12), `LATAM` (12), `Remote`, `Latin America`, `São Paulo`, `Americas Remote`, `Remote - Brazil`, `Colombia, Brazil, Argentina, Uruguay (Remote)`.
- `published_at` e `first_seen_at` são ISO-8601 com fuso. `first_seen_at` é a entrada no catálogo e às vezes cai dias depois da publicação (ex.: publicada em 17/11, vista em 23/11).
- `url` é `https://rebasedev.com.br/jobs/<slug>`. Os domínios de `apply_url` são `jobs.ashbyhq.com` (82), `job-boards.greenhouse.io` (47), `jobs.lever.co` (32), `apply.workable.com` (28), além de Teamtailor, Workday e outros.
- `company` é `{name, slug}`.
- `agent/jobs` acrescenta `description`, `description_md`, `closed_at` e `tambem_publicada`.

**Limite de taxa**: o `X-RateLimit-Remaining` caiu 1 por chamada, de 59 até 50. Sobra margem.
