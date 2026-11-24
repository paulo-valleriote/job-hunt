# Spec: Catálogo Rebase como fonte única por script no `/busca`

**Status:** ready-for-agent

> Origem: mapa `.scratch/rebase-jobs/map.md` e os tickets resolvidos 01 a 09 dessa pasta (decisões de 2026-11-24).
> Substitui: a spec `.scratch/fontes-gratuitas-vagas/spec.md` (Greenhouse, Lever, Ashby, Himalayas), que fica como histórico.
> Idioma: pt-BR; identificadores de código em inglês. Vocabulário do `GLOSSARY.md`: **Fonte**, **Catálogo Rebase**, **Rodada**.

## Problem Statement

Hoje o `/busca` tem duas coletas: o LinkedIn, pelo navegador, e uma coleta por script que consulta os ATS de uma lista de empresas (Greenhouse, Lever, Ashby, a partir de `fontes_ats.json`) e o agregador Himalayas. A coleta por script dá trabalho e rende pouco. A lista de tokens precisa ser mantida à mão (`/descobrir-token`), tokens quebram com 404, e a elegibilidade para quem mora no Brasil tem de ser deduzida de campos de localização que nem sempre existem, o que faz muita vaga ser descartada por "elegibilidade não confirmada". Também há um cache próprio do Himalayas e regras de pausa por fonte para manter.

Existe agora o **Catálogo Rebase**: cerca de 670 vagas remotas de dev em empresas de fora que contratam quem mora no Brasil, curadas e atualizadas duas vezes por dia, com uma API REST autenticada por token pessoal. Ele cobre os mesmos ATS (Ashby, Greenhouse, Lever, Workable e outros) e já garante remoto e elegibilidade para o Brasil. O usuário quer trocar toda a coleta por script por esse catálogo, sem perder as regras que já valem no `/busca` e sem mexer no fluxo do LinkedIn.

## Solution

A coleta por script do `/busca` passa a ler só o Catálogo Rebase (`https://rebasedev.com.br/api/v1`), com o token guardado em `private/rebase.env`. A consulta é ampla, por stack (vinda do `stack_desejada` do `busca.yaml`), e o resto do recorte (nível, título, janela, empresas excluídas) é feito localmente pelas regras que já existem. Cada vaga do catálogo vira um registro de vaga do `/busca` com `fonte: rebase`, link de candidatura do ATS e a página do Rebase como atribuição. O LinkedIn continua igual, mas pula na verificação as vagas que o Rebase já trouxe, e na duplicata fica a do Rebase.

Greenhouse, Lever, Ashby, Himalayas, `fontes_ats.json`, `/descobrir-token`, o cache do Himalayas e os testes deles saem do repositório (o histórico fica no git). A integração é só leitura: nada é escrito na conta do Rebase. O Guardrail 7 é ampliado para permitir que senioridade e stack do `busca.yaml` vão nas consultas externas. O `/triagem` passa a ler a descrição de uma vaga do Rebase pela página markdown pública do catálogo.

## User Stories

### Coleta

1. Como usuário, quero que o `/busca` colete vagas do Catálogo Rebase por script, sem navegador, para a rodada ser rápida e não gastar a cota da assinatura.
2. Como usuário, quero que a coleta use a minha stack desejada do `busca.yaml` como filtro da consulta, para trazer só vagas que tenham pelo menos uma das tecnologias que eu procuro.
3. Como usuário, quero escrever a stack como estou acostumado (ex.: "Golang", "Node.js"), para não precisar decorar os slugs do Rebase.
4. Como usuário, quero que uma stack que não exista no catálogo faça o `make check-config` falhar com uma mensagem clara, para corrigir o `busca.yaml` antes da rodada em vez de receber zero vagas sem explicação.
5. Como usuário, quero que a consulta não filtre por nível na API, para não perder as vagas que vêm sem senioridade preenchida.
6. Como usuário, quero que vagas do Rebase de nível sênior, staff ou liderança sejam descartadas com o motivo "nível acima do alvo (<nível>)", para não triar vaga fora do meu alvo.
7. Como usuário, quero que vagas do Rebase sem nível preenchido continuem na rodada, para eu decidir pelo anúncio.
8. Como usuário, quero que a coleta leia até 10 páginas de 50 vagas, para cobrir o catálogo relevante sem estourar o limite de 60 requisições por minuto.
9. Como usuário, quero que a janela "desde a última busca" seja aplicada pela data em que a vaga entrou no catálogo, para ver as vagas novas no Rebase mesmo que tenham sido publicadas dias antes.
10. Como usuário, quero que os filtros locais de título (`titulos_incluidos`/`titulos_excluidos`) valham para as vagas do Rebase, para manter o recorte por cargo que já uso.
11. Como usuário, quero que empresas de `vagas_excluidas.md` nunca apareçam, venham do Rebase ou do LinkedIn, para respeitar o Guardrail 4.
12. Como usuário, quero que vaga do Rebase sem link de candidatura seja descartada com motivo, para não gravar vaga em que não consigo me candidatar.
13. Como usuário, quero que a coleta nunca escreva nada na minha conta do Rebase, para nenhuma ação ser feita em meu nome.

### Registro da vaga

14. Como usuário, quero que o link de cada vaga do Rebase aponte para a candidatura oficial no ATS da empresa, para me candidatar direto.
15. Como usuário, quero que a página da vaga no Rebase fique guardada como atribuição, para eu poder ler o anúncio completo e ter a origem registrada.
16. Como usuário, quero que as vagas do Rebase entrem como remotas e elegíveis ao Brasil, com evidência citando o catálogo e a localização, para não serem descartadas pela regra de remoto por falta de dado.
17. Como usuário, quero ver os requisitos principais da vaga (as skills principais do catálogo) no arquivo do dia, para fazer uma primeira triagem rápida.
18. Como usuário, quero ver o modelo de contratação e o salário quando o catálogo trouxer, para saber de cara se é PJ ou CLT e quanto paga.
19. Como usuário, quero que o arquivo do dia mostre requisitos e trecho juntos, sem um esconder o outro, para não perder o salário quando houver requisitos.
20. Como usuário, quero que a data de uma vaga do Rebase seja mostrada como "entrou no Rebase em", para não confundir com a data de publicação.
21. Como usuário, quero ver `rebase` como fonte da vaga, para saber de onde ela veio.
22. Como usuário, quero que a tela de vagas (`ui/`) continue funcionando com as vagas do Rebase, sem mudança, para não perder a ferramenta que já uso.

### Convivência com o LinkedIn

23. Como usuário, quero que o fluxo do LinkedIn pelo navegador continue como hoje, para não perder vagas que só existem lá.
24. Como usuário, quero que a coleta do Rebase rode antes do LinkedIn, para o LinkedIn saber o que já foi trazido.
25. Como usuário, quero que o `/busca` não abra no navegador vagas do LinkedIn que o Rebase já trouxe (mesma empresa e título), para economizar tempo e cota.
26. Como usuário, quero que o fechamento da rodada diga quantas vagas do LinkedIn foram puladas por "já veio do Rebase", para saber que o corte aconteceu.
27. Como usuário, quero que, na duplicata entre Rebase e LinkedIn, fique a vaga do Rebase e o LinkedIn apareça como fonte secundária, para ter o link do ATS e ainda saber que ela também está no LinkedIn.
28. Como usuário, quero que o teto de 50 vagas gravadas por rodada continue, dividido em rodízio igual entre Rebase e LinkedIn, com a sobra de uma fonte indo para a outra, para nenhuma fonte dominar a rodada.

### Falhas e limites

29. Como usuário, quero que o `make check-config` barre a rodada se o token não estiver em `private/rebase.env`, com instrução de onde gerar e como gravar, para eu resolver antes de começar.
30. Como usuário, quero que um token recusado (401) vire falha de fonte com o motivo "token recusado (401)" e o link para gerar outro, para a rodada seguir com o LinkedIn e eu saber o que fazer.
31. Como usuário, quero que a falta do aceite de Novidades (403) vire falha de fonte com o link da página de aceite, para eu corrigir a conta.
32. Como usuário, quero que, no limite de taxa (429), o script espere e tente a mesma página uma vez se a espera pedida for de até 60 s, para não perder a rodada por um pico.
33. Como usuário, quero que um 429 repetido, ou com espera acima de 60 s, vire falha de fonte, para a rodada não travar.
34. Como usuário, quero que erro de rede, 5xx ou JSON inválido vire falha de fonte sem nova tentativa, como hoje, para a rodada seguir.
35. Como usuário, quero que as páginas já lidas sejam mantidas quando a leitura falhar no meio, e que o motivo diga em que página parou, para não perder o que já veio.
36. Como usuário, quero que o token nunca apareça em mensagem de erro, log, stderr ou arquivo gravado, para ele não vazar (Guardrail 10).
37. Como usuário, quero que o `make doctor` diga se o token está ok, recusado (401) ou sem aceite (403), com uma única chamada, para diagnosticar a conta rápido.

### Triagem

38. Como usuário, quero que o `/triagem` de uma vaga do Rebase leia o anúncio pela página markdown pública do catálogo, sem token, para ter a descrição completa mesmo quando o ATS (ex.: Ashby) vem vazio.
39. Como usuário, quero que, se a página do Rebase falhar, o `/triagem` tente o link do ATS e, por último, peça que eu cole o texto, como hoje.
40. Como usuário, quero que a triagem avise com destaque no topo quando a página disser que a vaga foi encerrada, e siga mesmo assim, para eu decidir.

### Remoção e higiene

41. Como mantenedor, quero que Greenhouse, Lever, Ashby, Himalayas, a lista de tokens, o `/descobrir-token`, o cache do Himalayas e os testes deles saiam do repositório, para não manter código morto.
42. Como mantenedor, quero que as funções reaproveitáveis da coleta antiga (requisição HTTP e tradução de erro em motivo de falha) sejam movidas para o novo módulo, para não reescrever o que funciona.
43. Como mantenedor, quero que o resumo da rodada perca a seção "Tokens com 404", para não mostrar uma seção que não faz mais sentido.
44. Como mantenedor, quero que o comando `/busca` e a sua documentação falem em "Rebase" em vez de "fontes de ATS e agregador", para a instrução bater com o que o script faz.
45. Como usuário, quero que o Guardrail 7 diga explicitamente que senioridade e stack do `busca.yaml` podem ir em consultas externas e que `minhas_skills` continua proibido, para a regra cobrir o que o script envia.
46. Como mantenedor, quero que as permissões de WebFetch dos hosts removidos saiam do `.claude/settings.json` e que o host do Rebase seja liberado para o `/triagem`, para as permissões refletirem as fontes reais.

## Implementation Decisions

### Módulo novo: adaptador do Catálogo Rebase

- Um módulo de script novo, dono de tudo que é Rebase: ler o token, montar a consulta, paginar, tratar erros e traduzir cada vaga em registro de vaga do `/busca`. É o único módulo que fala com a API.
- Interface pública (a seam de teste): uma função de coleta que recebe a configuração já lida (stack traduzida, janela `desde`), o token e as dependências injetáveis `fetch` e `sleep`, e devolve `{vagas, falhas}`, o mesmo formato que o `busca.py coletar` grava hoje. Segue o padrão de injeção que a coleta antiga já usa.
- Funções auxiliares expostas para o `check-config` e o `doctor`: ler o token de `private/rebase.env` (variável `TOKEN`, não `REBASE_TOKEN`), traduzir `stack_desejada` em slugs, e testar o token com uma chamada.
- `http_get` e `motivo_da_falha` saem da coleta antiga e passam a morar aqui (ou num utilitário que ele importa).

### Consulta

- Endpoint: `GET /api/v1/jobs`, com `Authorization: Bearer <token>`, `por_pagina=50`, um parâmetro `skill` repetido por slug, `skills_modo` no padrão (qualquer uma). Sem `q`, sem `nivel`, sem `modelo`. Não usa `/agent/jobs` (cerca de 10 vezes mais pesado) nem lê a descrição na busca.
- `cargos_alvo` não vai para o Rebase; continua servindo só para o LinkedIn.
- Leitura sempre até o teto de **10 páginas** (500 vagas, 10 requisições), ou até a última página, o que vier antes. Não há parada antecipada, porque a janela corta por `first_seen_at` e a listagem é ordenada por `published_at`.
- Tradução da stack: normalização (sem caixa, sem acento, sem pontuação) mais uma tabela pequena de apelidos (ex.: golang→go, node.js→nodejs). Slugs confirmados: `go`, `typescript`, `nodejs`, `aws`. O resultado é conferido contra a lista de skills do `GET /api/v1/meta`.
- `minhas_skills` (perfil guardado na conta do Rebase) nunca é usado.

### Tradução vaga do Rebase → registro de vaga

| Campo | Valor |
|---|---|
| `titulo` | `title` |
| `empresa` | `company.name` |
| `link` | `apply_url`. Vaga com `apply_url` nulo é descartada com motivo. |
| `atribuicao` | `url` (página da vaga no Rebase, `https://rebasedev.com.br/jobs/<slug>`) |
| `local` | `location`, literal (texto livre do ATS) |
| `modalidade` | `remoto` (garantia do catálogo) |
| `elegibilidade` | `brasil` (garantia do catálogo; `hires_in_brazil` vem como string `"yes"`) |
| `evidencia` | `Rebase: contrata quem mora no Brasil (<location>)` |
| `data` | AAAA-MM-DD de `first_seen_at` |
| `requisitos` | `Requer: ` + `skills_principais` separados por vírgula; vazio se a lista vier vazia |
| `trecho` | modelo de contratação e salário, quando houver (ex.: `PJ · USD 5000–7000/mês`); vazio se não houver |
| `status` | `aberta` |
| `candidatura` | `externa` |
| `fonte` | `rebase` |

- Filtro de nível local, na tradução ou logo depois dela: `seniority` vem **com acento** (`júnior`, `pleno`, `sênior`, `staff`, `liderança` ou `null`). Ficam `júnior`, `pleno` e `null`. `sênior`, `staff` e `liderança` são descartados com o motivo `nível acima do alvo (<nível>)`. No LinkedIn, que não traz o nível como campo, a regra continua só pelo título.

### Erros, limite de taxa e token

- Token ausente (arquivo ou linha `TOKEN=`): o `make check-config` falha com "gere o token em https://rebasedev.com.br/jobs/perfil/agentes e grave TOKEN= em private/rebase.env". O `/busca` para no gate.
- 401 → falha de fonte `token recusado (401): gere outro em https://rebasedev.com.br/jobs/perfil/agentes`.
- 403 → falha de fonte `aceite de Novidades ausente (403): https://rebasedev.com.br/jobs/perfil/aceite`.
- 429 → se `Retry-After` ≤ 60 s, espera e tenta a mesma página uma única vez; se repetir ou a espera passar de 60 s, falha de fonte.
- Rede, 5xx, JSON inválido → falha de fonte, sem nova tentativa.
- Em qualquer falha, as vagas das páginas já lidas são mantidas e o motivo diz em que página a leitura parou.
- O token nunca aparece em motivo, log, stderr ou arquivo gravado.
- Sem cache para o Rebase.

### Mudanças no `busca.py`

- `coletar`: passa a chamar o adaptador do Rebase. O argumento `--fontes` sai. A saída `{vagas, falhas}` não muda.
- `_prioridade`: prioridade 0 passa a ser `fonte == "rebase"`; LinkedIn fica em 1. A dedupe continua em `processar()` com as chaves link sem query e empresa+título normalizados; entre Rebase e LinkedIn só a segunda chave casa.
- `_rodizio` e o teto `MAX_VAGAS` (50) não mudam; as fontes passam a ser `rebase` e `linkedin`.
- `candidatos`: ganha `--coletadas <json>`. Vaga da listagem do LinkedIn com a mesma empresa+título de uma vaga do Rebase sai antes da verificação, com o motivo "já veio do Rebase" no stderr.
- `resumo`: sai a seção "# Tokens com 404".
- `render`: `- Trecho:` passa a mostrar requisitos e trecho juntos (hoje `requisitos or trecho`). `- Data:` diz "entrou no Rebase em" nas vagas do Rebase. As chaves `Data` e `Trecho` são mantidas, porque o parser da `ui/` lê por chave.
- Docstrings e comentários que citam ATS, Himalayas e tokens são reescritos.

### Configuração e diagnóstico

- `make check-config` (validador de config): checa `private/rebase.env`/`TOKEN` e valida `stack_desejada` contra as skills do `/api/v1/meta`. Nenhum campo novo no `busca.yaml`; o `busca.example.yaml` não muda de forma.
- `make doctor`: confere arquivo e `TOKEN` e faz `GET /api/v1/jobs?por_pagina=1`. Saída: `ok`, `token recusado (401)` ou `sem aceite (403)`.

### Instruções e regras

- `.claude/commands/busca.md`: descrição e passo 2 falam em Rebase; passo 6 passa `--coletadas` ao `candidatos`; o passo 9 perde "Tokens com 404 / revisão de fontes_ats.json"; o fechamento relata os cortes "já veio do Rebase".
- `.claude/commands/triagem.md`, passo 2: "vaga com `Atribuição` do Rebase (ou link `rebasedev.com.br/jobs/…`) → leia `<url>.md` primeiro, depois o link do ATS, depois peça o texto colado; se a página disser que a vaga foi encerrada, avise com destaque no topo e siga". O `scripts/triagem.py` não muda.
- `.claude/settings.json`: saem as quatro permissões `WebFetch(domain:…)` de greenhouse, lever, ashby e himalayas; entra `WebFetch(domain:rebasedev.com.br)` para o `/triagem`. O script usa urllib e não precisa de permissão de WebFetch.
- `CLAUDE.md`, Guardrail 7, nova redação: "Consultas externas (WebSearch, URLs de busca no navegador, APIs de fonte) **não** podem conter dados pessoais: só cargo, local, regime, senioridade e stack vindos do `busca.yaml`. O `minhas_skills` do Rebase (perfil guardado na conta) continua proibido."

### Remoção

- Saem: o módulo de coleta de ATS, o módulo do Himalayas, o módulo de fontes e `fontes_ats.json`, o comando `/descobrir-token`, os testes de fontes, e a classe de testes de fontes ATS dentro dos testes do `busca`. O cache local `private/cache/himalayas.json` é apagado à mão (fora do git).
- Ficam sem mudança: `ui/`, `scripts/enviei.py` (`--fonte` é texto livre), `scripts/triagem.py`, o `Makefile`, `vendor/` e a pasta `.scratch/fontes-gratuitas-vagas/` (histórico).

## Testing Decisions

- **Bom teste**: exercita só comportamento externo, pela interface pública, com respostas HTTP falsas injetadas por `fetch` e um `sleep` falso que registra as esperas. Não depende de rede, de token real nem de detalhes internos (nomes de funções privadas, ordem de chamadas internas além do que o contrato da API define). Nunca usa dados de `private/`.
- **Seam principal (nova, uma só)**: a função de coleta do adaptador Rebase, `(config, token, fetch, sleep) → {vagas, falhas}`. Cobre:
  - montagem da consulta (slugs repetidos, `por_pagina=50`, sem `q`/`nivel`, header Bearer);
  - paginação até 10 páginas ou até a última;
  - tradução de cada campo do registro, incluindo `requisitos` vazio, `trecho` com e sem salário/modelo, `data` vinda de `first_seen_at`;
  - descarte por `apply_url` nulo e por nível (`sênior`, `staff`, `liderança`), com o nível acentuado; `null` fica;
  - 401, 403, 5xx, rede, JSON inválido, 429 com `Retry-After` ≤ 60 (uma nova tentativa), 429 repetido e 429 com espera > 60;
  - manutenção das páginas já lidas e página de parada no motivo;
  - token ausente de qualquer motivo, stderr ou saída.
- **Seams existentes, reaproveitadas**: `processar()` (dedupe, prioridade, rodízio, teto), `render()`/`resumo()` e a CLI do `busca.py` por subprocess, como nas classes `DedupeEntreFontes`, `Render` e `Cli` dos testes do `busca`. Os testes de dedupe e rodízio que hoje usam `fonte="greenhouse:…"`, `lever` e `himalayas` são reescritos com `fonte="rebase"`, mantendo os mesmos comportamentos. Entram casos para `candidatos --coletadas` (corte "já veio do Rebase") e para o `render` mostrando requisitos e trecho juntos e "entrou no Rebase em".
- **Tradução da stack e check-config**: testes no estilo dos testes do validador de config já existentes, com a lista de skills do `/meta` injetada (sem rede): apelidos, normalização, stack desconhecida falha com mensagem clara, token ausente falha com instrução.
- **Doctor**: segue o estilo do teste em shell do doctor já existente, com a chamada à API substituída por um falso que devolve 200, 401 ou 403.
- **Prior art**: a coleta antiga já injeta `fetch` e `sleep` (`coletar_todas`), e os testes de fontes faziam o mesmo; o novo teste do adaptador segue esse padrão e substitui os testes de fontes.

## Out of Scope

- Escrever de volta no Rebase (acompanhar vaga, etapas, ocultar) a partir do `/enviei` ou de outro comando. A integração é só leitura.
- Novas fontes além do Catálogo Rebase e do LinkedIn.
- Registrar o MCP do Rebase (`https://rebasedev.com.br/mcp`) para consultas avulsas fora do `/busca`; fica para um esforço futuro, depois de usar o script na prática.
- Usar `/agent/jobs` ou a descrição das vagas na busca.
- Mudanças na `ui/`, no `scripts/enviei.py` e no `scripts/triagem.py`.
- Cache das respostas do Rebase.
- Usar `minhas_skills` ou qualquer dado do perfil guardado na conta do Rebase.

## Further Notes

- O token já existe e foi testado (2026-11-24): `GET /api/v1/jobs?por_pagina=1` autenticado respondeu 200 com 670 vagas. O aceite de Novidades está feito.
- Amostra autenticada (respostas cruas em `private/rebase-amostra/`, fora do git): nível júnior/pleno + as quatro skills dá 65 vagas; só as quatro skills, 389. Como o nível é filtrado localmente, a rodada deve ler bem mais que 65 antes do corte. `apply_url` veio preenchido em 214 de 214 vagas, mas o contrato diz que pode ser nulo.
- `first_seen_at` às vezes cai dias depois de `published_at`; a data mostrada passa a significar "entrou no Rebase em".
- Os termos do Rebase permitem uso pessoal e por agentes e proíbem republicar o catálogo e compartilhar o token. O arquivo do dia é local, em `private/`, e não é republicação.
- O `GLOSSARY.md` já foi atualizado na abertura do mapa (Fonte, Catálogo Rebase, Rodada).
