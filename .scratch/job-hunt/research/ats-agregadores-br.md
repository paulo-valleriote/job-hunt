# ATS públicos, agregadores e cobertura BR/LATAM: fechamento de lacunas

- Data da consulta: 2026-11-11 (medições entre 12:49 e 12:55 UTC)
- Complementa: `.scratch/job-hunt/research/busca-gratuita.md` (não substitui; aqui estão as lacunas fechadas e as medições).
- Escopo: APIs públicas de ATS, agregadores de vagas remotas e páginas de carreiras de empresas brasileiras.
- Regras seguidas: só fontes primárias (documentação do fornecedor, termos, robots.txt, resposta da própria API, página de carreiras da empresa). Nada de endpoint ou token inventado. Consultas externas só com termos genéricos. Nenhum dado pessoal foi usado. `private/` e `profile_truth.md` não foram lidos.
- Marcação: **verificado** = visto nesta consulta na fonte; **não verificado** = não confirmado; **citação via busca** = trecho de resultado de busca, não da página primária.
- Saídas brutas: `/tmp/claude-1000/-home-pmv-programming-job-hunt/d882d91e-a328-42c4-b860-23f507f2480a/scratchpad/` (fora do repositório).

## Resumo executivo

1. **Gratuito de fato, sem chave: sim** para Greenhouse (Job Board API), Ashby (Public Job Posting API), Lever (Postings API, v0), Himalayas, Remotive, RemoteOK e Arbeitnow. Todos responderam a GET sem autenticação nesta consulta. Gupy **não** tem leitura pública sem token: a API exige Bearer token de cliente Premium/Enterprise.
2. **Cobertura BR: boa nos ATS, a partir de empresas escolhidas.** Confirmei boards reais com centenas de vagas no Brasil: Stone (Greenhouse, 324 de 349 com localização brasileira), C6 Bank (157 de 158), Inter (113 de 120), QuintoAndar (82 de 103), Ebanx (22 de 36), Gympass/Wellhub, VTEX, RD Station, Nubank (Ashby), Neon (Lever).
3. **Agregadores: cobertura BR baixa.** Himalayas é o único com filtro de país (`country=Brazil`) e `worldwide=true`, e cobre vagas "worldwide" (medido: 820 vagas com `worldwide=true`; 5.835 com `country=Brazil`, que inclui as mundiais). Remotive (13 vagas no feed inteiro), RemoteOK (99), Arbeitnow (300, quase todas na Europa) e We Work Remotely (100, metade "Anywhere in the World") têm pouco ou nada de Brasil/LATAM.
4. **Gupy, o ATS mais usado no Brasil, não entra em integração automática.** Não há leitura pública sem token e os termos de candidato proíbem "agregar, copiar ou duplicar partes" da plataforma. Só lista manual de links.
5. **Recomendação:** integrar primeiro Greenhouse + Ashby + Lever (adaptador por ATS, lista de tokens confirmados) e Himalayas (filtro Brasil + worldwide, com atribuição). Remotive, RemoteOK e WWR entram depois, se o ganho justificar. Arbeitnow e Gupy ficam fora.

## Tabela 1: fontes

| Fonte | Gratuito e sem chave (leitura) | Cobertura BR/LATAM/worldwide | Limites | Termos e atribuição (citação) | Esforço | Veredito |
|---|---|---|---|---|---|---|
| **Greenhouse Job Board API** | Sim. "Job Board data is publicly available, so authentication is not required for any GET endpoints." ([docs.greenhouse.io/job-board.html](https://docs.greenhouse.io/job-board.html), verificado) | Depende do board escolhido. Medido: Stone, C6, Inter, QuintoAndar, Ebanx, Gympass, VTEX, RD Station (ver Tabela 3) | Não encontrados na página (verificado: "The page doesn't mention any rate limit."). Ver lacunas | Não há termos de atribuição na página | Baixo: 1 GET por token. Campo `location.name` é texto livre (ex.: "Remoto", "Sao Paulo, Sao Paulo, Brasil") | **Integrar** |
| **Ashby Public Job Posting API** | Sim na prática: GET sem chave retornou 200 (Nubank: 109 vagas). A doc mostra o `curl` sem header e **não diz** que não exige autenticação. "The page doesn't say whether authentication or an API key is required." ([developers.ashbyhq.com/docs/public-job-posting-api.md](https://developers.ashbyhq.com/docs/public-job-posting-api.md), updatedAt 2026-10-23) | Depende do board. Nubank: 34 vagas em São Paulo entre 109 | Não informados | Sem termos na página | Baixo: 1 GET por nome de board. Traz `isRemote`, `workplaceType`, `address`, `secondaryLocations` | **Integrar** (confirmar sem chave na doc é lacuna, mas a medição não exige chave) |
| **Lever Postings API (v0)** | Sim. README oficial: `GET /v0/postings/SITE?skip=X&limit=Y`; "To use the POST API, you need an API key." (POST é que exige chave). GET sem chave retornou 200 (Neon: 9 vagas). ([github.com/lever/postings-api](https://github.com/lever/postings-api), verificado) | Depende do site. Neon: 7 "Remoto" e 2 São Paulo. Página de docs em hire.lever.co pede login (verificado: redireciona para `auth/login`) | Não há limite de GET no README. Limite só para POST de candidatura: "more than 2 application POST requests per second" dá 429 | README oficial; sem termos de atribuição encontrados | Baixo: `GET https://api.lever.co/v0/postings/{site}?mode=json`. EU: `api.eu.lever.co` (citado no README) | **Integrar** |
| **Gupy** | **Não.** API exige Bearer: "Authorization" header em `GET /api/v1/jobs` ([developers.gupy.io/reference/authentication.md](https://developers.gupy.io/reference/authentication.md)). "The Gupy API is available to customers on the Premium and Enterprise plans." Token é de cliente, não do candidato | Brasil: muito forte (PagBank/PagSeguro, Creditas) mas sem API sem token | Limite WAF de 500 req/min por IP ([developers.gupy.io/reference/rate-limiting.md](https://developers.gupy.io/reference/rate-limiting.md)) | Termos do candidato ([gupy.io/termos-de-uso-recrutamento-e-selecao-candidatos](https://www.gupy.io/termos-de-uso-recrutamento-e-selecao-candidatos)), citação extraída pela ferramenta, conferir no original: proibido "agregar, copiar ou duplicar partes do Gupy Recrutamento e Seleção, incluindo oportunidades de trabalho expiradas;". Nenhuma cláusula sobre robôs ou raspagem | Alto e arriscado | **Não integrar.** Só links manuais |
| **Remotive API** | Sim: `https://remotive.com/api/remote-jobs` respondeu 200 sem chave (verificado) | Medido: 13 vagas no total (`total-job-count`); 9 "Worldwide", 0 BR/LATAM. `search=brazil` devolveu as mesmas 13 (o parâmetro não filtrou) | "we advise max. 4 times a day"; "excessive requests (more than 2x per minute) will be blocked" (campo `0-legal-notice` da própria API, verificado) | "Please link back to the URL found on Remotive AND mention Remotive as a source"; "Jobs displayed are delayed by 24 hours"; "Please do not submit Remotive jobs to third Party websites, including ... Google Jobs, LinkedIn Jobs." | Baixo | Baixo valor. Só se quiser remoto global |
| **Himalayas API** | Sim, sem chave: "Both the browse endpoint and the search endpoint are free to use." e "Do I need an API key...? No. Both endpoints work without a key or sign-up." ([himalayas.app/docs/remote-jobs-api](https://himalayas.app/docs/remote-jobs-api), verificado) | **Melhor agregador para BR.** `country=Brazil`: totalCount 5.835. `worldwide=true`: totalCount 820. Nas 20 da amostra de Brasil, 9 têm lista de países incluindo Brazil e 11 têm lista vazia (= worldwide) | Sem chave: "share one public allowance with every other caller". Com chave gratuita: "60 requests per minute and 10,000 per UTC day". Cache: "refreshed every 24 hours" | "Every Apply action must use the API's applicationLink, not a direct employer/ATS link."; "Display visible Himalayas source credit."; "Do not pass them on to other job boards, aggregators, Google Jobs or LinkedIn Jobs, including through feeds or JobPosting structured data." | Baixo-médio. Paginação por `cursor` (`offset` descontinuado) | **Integrar** com atribuição visível e cache de 24 h |
| **RemoteOK API** | Sim: `https://remoteok.com/api` respondeu 200 (verificado) | Medido: 99 vagas; 3 "Anywhere in the World"; 10 com "Brazil/LATAM" no texto (loc+descrição). Baixo | Não encontrado no bloco lido e no robots (**não verificado**) | Campo `legal` da própria API: "Please link back (with follow, and without nofollow!) to the URL on Remote OK and mention Remote OK as a source, so we get traffic back from your site. If you do not we'll have to suspend API access." e "Please don't use the Remote OK logo without written permission". robots.txt: `Content-Signal: search=yes,ai-train=no,use=reference` | Baixo | Opcional, com atribuição |
| **We Work Remotely (RSS)** | Feed em `https://weworkremotely.com/remote-jobs.rss` respondeu 200 (verificado). Páginas de termos e de RSS deram **403** para o nosso acesso (não verificado na primária) | Medido: 100 itens; `region` "Anywhere in the World" 50, "USA Only" 45, "Europe Only" 2; 3 com Brasil/LATAM no texto | Não verificado | Citação via busca (não primária): "anyone can use the feed, all we ask is that you attribute the links back to We Work Remotely" e, na API, "scraping, copying, saving, or storing our data is strictly prohibited". **Não verificado** na página primária | Baixo | **Não integrar** até ler os termos. O campo `region` é útil se liberado |
| **Arbeitnow Job Board API** | Sim: `https://www.arbeitnow.com/api/job-board-api` respondeu 200 (verificado) | Medido: 300 vagas na página 1; 14 `remote=true`; 2 com Brasil/LATAM no texto; localização majoritária Berlim, Paris, Londres, Amsterdã. **Fraco para BR** | Atualização "every hour" (`meta.info`) | `meta.terms`: "This is a free public API for jobs, please do not abuse. I would appreciate linking back to the site. By using the API, you agree to the terms of service present on Arbeitnow.com" (verificado). Página de termos não lida | Baixo | Fora (cobertura) |
| **Gupy job pages (HTML público)** | Páginas `portal.gupy.io/job/...` têm JSON-LD `JobPosting` com `jobLocation` (ex.: "Diadema, São Paulo, Brasil") e `validThrough` (verificado em uma página). `portal.gupy.io/robots.txt`: "User-agent: *" com "Disallow:" vazio | Brasil forte | N/A | O JSON-LD existe para indexação. Isso não autoriza copiar em massa; ver termos acima | Médio (scraping) | **Fora**: contraria o spec (sem scraping por script) e os termos |
| **InHire, Workable, Recruitee, SmartRecruiters, Kenoby, Solides, Pandapé, Vagas.com, Catho** | Não testados por API. Apenas InHire apareceu (link 110 vezes em `olist.com/carreiras`) | BR | N/A | N/A | N/A | **Não verificado** |

Observação sobre o Greenhouse: o host de vagas muda entre `boards.greenhouse.io` e `job-boards.greenhouse.io`, mas o token é o mesmo (`boards-api.greenhouse.io/v1/boards/{token}/jobs`). Ex.: Inter aparece como `boards.greenhouse.io/inter`.

## Tabela 2: empresa → ATS → token → endpoint → testado

Legenda: "testado: sim" = GET público respondeu 200 **e** o conteúdo das vagas confirma a empresa (URL ou localização). "vínculo com página oficial" = a página de carreiras da própria empresa aponta para o ATS (verificado por HTML). Data: 2026-11-11, ~12:50 UTC.

| Empresa | ATS | Evidência da página oficial | Board token / URL | Endpoint público | Testado | Nº vagas medido | Vínculo com página oficial |
|---|---|---|---|---|---|---|---|
| Ebanx | Greenhouse | `ebanx.com/careers` (200) contém `boards.greenhouse.io/ebanx` (12 ocorrências) | `ebanx` / job-boards.greenhouse.io/ebanx | `https://boards-api.greenhouse.io/v1/boards/ebanx/jobs` | sim | 36 (22 com localização BR) | sim |
| Neon | Lever | `neon.com.br/carreiras` (200) contém `jobs.lever.co/neon` (3) | `neon` / jobs.lever.co/neon | `https://api.lever.co/v0/postings/neon?mode=json` | sim | 9 (7 "Remoto", 2 São Paulo) | sim |
| PagBank (PagSeguro) | Gupy | `pagbank.com.br/carreiras` (200) contém `pagseguro.gupy.io` (4) | `pagseguro` / pagseguro.gupy.io | Gupy API exige token (não chamada). Página pública: `pagseguro.gupy.io/jobs` (200) | não (API) / sim (página) | n/d | sim |
| Creditas | Gupy | `creditas.gupy.io` (200, página de empresa "Creditas Soluções Financeiras"). Link apareceu em `creditas.com/carreiras`, que retornou **404** | `creditas` / creditas.gupy.io | Gupy API exige token | não (API) | n/d | fraco (página 404) |
| Nubank | Ashby | Homepage `nubank.com.br` (200) sem link ATS. Vínculo com a página oficial **não verificado** | `nubank` / jobs.ashbyhq.com/nubank | `https://api.ashbyhq.com/posting-api/job-board/nubank` | sim | 109 (34 São Paulo, 22 Palo Alto, 15 Miami) | não (só pela URL de vaga) |
| Nubank (Greenhouse) | Greenhouse | — | `nubank` | `boards-api.greenhouse.io/v1/boards/nubank/jobs` | sim (vazio) | 0 | — |
| QuintoAndar | Greenhouse | `quintoandar.com.br/carreiras` **404**. Vínculo não verificado pela página | `quintoandar` / job-boards.greenhouse.io/quintoandar | boards-api.greenhouse.io/v1/boards/quintoandar/jobs | sim | 103 (82 Brasil/São Paulo) | não |
| Stone | Greenhouse | `stone.com.br/carreiras` (200) sem link ATS no HTML | `stone` / job-boards.greenhouse.io/stone | boards-api.greenhouse.io/v1/boards/stone/jobs | sim | 349 (324 Brasil) | não (confirmado só pelo conteúdo) |
| Gympass / Wellhub | Greenhouse | `wellhub.com/pt-br/carreiras` **403**. Vínculo não verificado | `gympass` (nome antigo) | boards-api.greenhouse.io/v1/boards/gympass/jobs | sim | 83 ("Brazil (Remote)" 19, Brazil SP 10) | não (confirmado só pelo conteúdo) |
| VTEX | Greenhouse | `vtex.com/br-pt/carreiras/` **404**. Vínculo não verificado | `vtex` / job-boards.greenhouse.io/vtex | boards-api.greenhouse.io/v1/boards/vtex/jobs | sim | 34 (19 Brasil) | não |
| Inter | Greenhouse | `bancointer.com.br/carreiras` **404**. Vínculo não verificado | `inter` / boards.greenhouse.io/inter | boards-api.greenhouse.io/v1/boards/inter/jobs | sim | 120 (113 Belo Horizonte/São Paulo) | não |
| C6 Bank | Greenhouse | `c6bank.com.br/carreiras` **403**. Vínculo não verificado | `c6bank` / job-boards.greenhouse.io/c6bank | boards-api.greenhouse.io/v1/boards/c6bank/jobs | sim | 158 (157 Brasil) | não |
| RD Station | Greenhouse | Página oficial não verificada | `rdstation` / job-boards.greenhouse.io/rdstation | boards-api.greenhouse.io/v1/boards/rdstation/jobs | sim | 4 (4 Brasil) | não |
| Loft | Ashby | `loft.com.br/carreiras` (200) sem link ATS | `loft` / jobs.ashbyhq.com/loft | api.ashbyhq.com/posting-api/job-board/loft | sim (board existe) | 0 hoje | não |
| Olist | InHire | `olist.com/carreiras` (200) contém `inhire.com.br` (110) | n/d | não testado (API pública não verificada) | não | n/d | sim (host) |
| Wildlife | não identificado | `wildlife.com/careers` **403**; greenhouse, lever e ashby `wildlife` deram 404 | n/d | n/d | não | n/d | não |
| Mercado Livre | não identificado | `careers.mercadolivre.com.br` sem resposta (DNS); greenhouse `mercadolibre` 404 | n/d | n/d | não | n/d | não |
| iFood | não identificado | `ifood.com.br/carreiras` **403**; greenhouse, lever e ashby `ifood` 404 | n/d | n/d | não | n/d | não |
| Hotmart | não identificado | `hotmart.com/pt-br/carreiras` **404**; greenhouse, lever e ashby 404 | n/d | n/d | não | n/d | não |
| Zenvia | não identificado | `zenvia.com/carreiras` **404**; greenhouse 404 | n/d | n/d | não | n/d | não |
| TOTVS | não identificado | `totvs.com/carreiras/` **404**; greenhouse `totvs` 404 | n/d | n/d | não | n/d | não |
| CloudWalk | não identificado | `cloudwalk.io/carreiras` **404**; greenhouse, lever e ashby 404 | n/d | n/d | não | n/d | não |
| Itaú | não identificado | `itau.com.br/carreiras` **403**; greenhouse `itau` 404 | n/d | n/d | não | n/d | não |
| Magalu | não identificado | `magazineluiza.com.br/carreiras` **403**; greenhouse `magalu` 404 | n/d | n/d | não | n/d | não |
| Locaweb | não identificado | `locaweb.com.br/carreiras` retornou 301 (redirect não seguido até o fim) | n/d | n/d | não | n/d | não |
| Dock | não identificado | `dock.tech/carreiras` **404**; greenhouse `dock` 404 | n/d | n/d | não | n/d | não |
| Pismo | não identificado | `pismo.io/careers` (200) sem link ATS; ashby `pismo` 404 | n/d | n/d | não | n/d | não |
| Cora | não identificado | `cora.com.br/carreiras` **404**; ashby `cora` 404 | n/d | n/d | não | n/d | não |
| Conta Azul | não identificado | `contaazul.com/carreiras` (200) sem link ATS | n/d | n/d | não | n/d | não |

Empresas sem evidência nesta consulta não entram na lista de integração. Não há token confirmado para Mercado Livre, iFood, Itaú, Magalu, Hotmart, Zenvia, TOTVS, CloudWalk, Dock, Cora, Locaweb, Pismo ou Conta Azul.

## Tabela 3: medições de cobertura (GET real, 2026-11-11)

| Fonte / chamada | HTTP | Total devolvido | Filtro BR/LATAM/worldwide | Observação |
|---|---|---|---|---|
| `boards-api.greenhouse.io/v1/boards/stone/jobs` | 200 | 349 | 324 com localização brasileira | maior board BR medido |
| `.../c6bank/jobs` | 200 | 158 | 157 Brasil | |
| `.../inter/jobs` | 200 | 120 | 113 BH/SP | |
| `.../quintoandar/jobs` | 200 | 103 | 82 Brasil/SP | |
| `.../gympass/jobs` | 200 | 83 | 36 Brasil; 50 com "remote"/LATAM no texto | |
| `.../ebanx/jobs` | 200 | 36 | 22 Brasil | |
| `.../vtex/jobs` | 200 | 34 | 19 Brasil | |
| `.../rdstation/jobs` | 200 | 4 | 4 Brasil | |
| `.../nubank/jobs` (Greenhouse) | 200 | 0 | — | board vazio |
| `api.ashbyhq.com/posting-api/job-board/nubank` | 200 | 109 | 34 São Paulo | `isRemote` disponível |
| `api.ashbyhq.com/posting-api/job-board/loft` | 200 | 0 | — | board existe, sem vagas |
| `api.lever.co/v0/postings/neon?mode=json` | 200 | 9 | 7 "Remoto" + 2 São Paulo | |
| `api.lever.co/v0/postings/nubank?mode=json` (e outros tokens) | 404 | — | — | token não existe em Lever |
| `himalayas.app/jobs/api?limit=20` | 200 | 20 (amostra) | — | feed geral |
| `himalayas.app/jobs/api/search?country=Brazil` | 200 | 20 (amostra) de **totalCount 5.835** | 9 com lista incluindo Brazil; 11 com lista vazia (worldwide) | cobertura real de BR: boa |
| `himalayas.app/jobs/api/search?worldwide=true` | 200 | 20 (amostra) de **totalCount 820** | todas com lista vazia | |
| `remotive.com/api/remote-jobs` | 200 | **13** no total | 9 "Worldwide"; 0 BR/LATAM | feed muito pequeno |
| `remotive.com/api/remote-jobs?search=brazil` | 200 | 13 | igual ao feed | `search` não filtrou |
| `remoteok.com/api` | 200 | 99 vagas (+1 metadado `legal`) | 3 "Anywhere in the World"; 10 com Brasil/LATAM no texto | |
| `arbeitnow.com/api/job-board-api` (página 1) | 200 | 300 (por página) | 14 `remote=true`; 2 Brasil/LATAM no texto | Europa predominante |
| `weworkremotely.com/remote-jobs.rss` | 200 | 100 itens | `region` "Anywhere in the World" 50; "USA Only" 45; 3 Brasil/LATAM no texto | |
| `api.gupy.io/api/v1/jobs` | não chamado | — | — | exige Bearer; não chamado sem token |

Nota de método: a contagem de Brasil/LATAM usou regex com limite de palavra (`\b`). Uma primeira contagem sem limite de palavra casou "translating" com "latin" e foi descartada.

## Termos e atribuição: citações literais

- **Greenhouse** ([docs.greenhouse.io/job-board.html](https://docs.greenhouse.io/job-board.html)): "Job Board data is publicly available, so authentication is not required for any GET endpoints." Sem termos de uso na página.
- **Ashby** ([developers.ashbyhq.com/docs/public-job-posting-api.md](https://developers.ashbyhq.com/docs/public-job-posting-api.md)): "This API allows you to get data for all currently published Job Postings for your organization. If you host your own careers page, you can use this data to populate it." Sem frase sobre autenticação, limites ou atribuição.
- **Lever** ([github.com/lever/postings-api](https://github.com/lever/postings-api), README oficial, lido em raw): "To use the POST API, you need an API key, which a Super Admin of your account can generate". Sobre limite: "Lever will return a `429` status code ... if your custom job site issues more than 2 application POST requests per second." Não há frase de termo para o GET.
- **Lever, documentação v1** ([hire.lever.co/developer/documentation](https://hire.lever.co/developer/documentation)): a seção de introdução diz que "all requests must be authenticated". Isso vale para a API de dados (`api.lever.co/v1`), **não** para a Postings API v0. A página de docs pode exigir login e a seção de Postings não foi lida na íntegra.
- **Gupy, autenticação** ([developers.gupy.io/reference/authentication.md](https://developers.gupy.io/reference/authentication.md)): "The authentication in the API is done through Bearer access tokens (RFC 6750)." e "The Gupy API is available to customers on the Premium and Enterprise plans."
- **Gupy, termos do candidato** ([gupy.io/termos-de-uso-recrutamento-e-selecao-candidatos](https://www.gupy.io/termos-de-uso-recrutamento-e-selecao-candidatos)): citação extraída por ferramenta de leitura; conferir no original: "agregar, copiar ou duplicar partes do Gupy Recrutamento e Seleção, incluindo oportunidades de trabalho expiradas;" e "acessar dados de terceiros, servidores ou contas que não é autorizado a acessar;". Não há cláusula explícita sobre robôs ou raspagem. A busca pelo termo "raspagem" não achou cláusula própria.
- **Himalayas** ([himalayas.app/docs/remote-jobs-api](https://himalayas.app/docs/remote-jobs-api)): "Every Apply action must use the API's applicationLink, not a direct employer/ATS link. Display visible Himalayas source credit. You can show the jobs on your own job board, site or app without asking us first. Do not pass them on to other job boards, aggregators, Google Jobs or LinkedIn Jobs, including through feeds or JobPosting structured data." Também: "locationRestrictions: Array of countries where applicants must be based (empty array means worldwide)".
- **Remotive** (campo `0-legal-notice` em [remotive.com/api/remote-jobs](https://remotive.com/api/remote-jobs), verificado): "Please link back to the URL found on Remotive AND mention Remotive as a source in order to Remotive to get traffic from your listing." e "Jobs displayed are delayed by 24 hours" e "we advise max. 4 times a day" e "Displaying our jobs in order to collect signups/email addresses to show a listing constitutes a breach of our terms of services." Termos completos: remotive.com/api-documentation (não lido nesta consulta).
- **RemoteOK** (campo `legal` em [remoteok.com/api](https://remoteok.com/api), verificado): "API Terms of Service: Please link back (with follow, and without nofollow!) to the URL on Remote OK and mention Remote OK as a source, so we get traffic back from your site. If you do not we'll have to suspend API access." e "Please don't use the Remote OK logo without written permission as it's a registered trademark, please DO use our name Remote OK though."
- **Arbeitnow** (campo `meta.terms` em [arbeitnow.com/api/job-board-api](https://www.arbeitnow.com/api/job-board-api), verificado): "This is a free public API for jobs, please do not abuse. I would appreciate linking back to the site. By using the API, you agree to the terms of service present on Arbeitnow.com". Os termos de Arbeitnow.com não foram lidos.
- **We Work Remotely**: as páginas [weworkremotely.com/remote-job-rss-feed](https://weworkremotely.com/remote-job-rss-feed), [weworkremotely.com/api-terms-and-guidelines](https://weworkremotely.com/api-terms-and-guidelines) e [weworkremotely.com/rss](https://weworkremotely.com/rss) retornaram **403** (não verificado na primária). Via busca (citação via busca, não primária): o feed permite uso "all we ask is that you attribute the links back to We Work Remotely", e a página de API proíbe "scraping, copying, saving, or storing our data". Os dois trechos não se conciliam sem leitura direta.
- **robots.txt**: RemoteOK (verificado): `Content-Signal: search=yes,ai-train=no,use=reference`, `Allow: /`. Gupy (`www.gupy.io/robots.txt`, verificado): regras por bot de IA e `Disallow` de utm, sem bloqueio geral de `/job`. Portal Gupy (`portal.gupy.io/robots.txt`): `User-agent: *` com `Disallow:` vazio. Robots não substituem os termos.

## Recomendação final (priorizada)

**Prioridade 1 (integrar primeiro)**

1. **Greenhouse** (`boards-api.greenhouse.io/v1/boards/{token}/jobs`) e **Lever** (`api.lever.co/v0/postings/{site}?mode=json`). Sem chave, documentados pelo fornecedor, com cobertura BR medida. Campo de localização é texto livre, então o filtro é por regex de Brasil/São Paulo/Remote/LATAM e por revisão humana na `elegibilidade`.
2. **Ashby** (`api.ashbyhq.com/posting-api/job-board/{name}`). Mesma lógica. Usa `isRemote` e `address` como sinal mais forte que o texto.
3. **Himalayas** (`/jobs/api/search?country=Brazil` e `?worldwide=true`, paginação por `cursor`). É o único agregador que filtra Brasil. Mandatório: link para `applicationLink`, crédito visível "Himalayas", sem repassar a agregadores, cache de 24 h.

**Prioridade 2 (opcional, com ganho pequeno)**

4. **RemoteOK**: 99 vagas, atribuição obrigatória (link com follow e citação do nome). Ganho baixo para BR.
5. **Remotive**: 13 vagas. Não justifica o custo; só se o usuário quiser remoto global.

**Fora**

6. **Gupy**: sem leitura pública sem token e termos que proíbem copiar partes da plataforma. Só links manuais. Se a vaga vier de uma página Gupy, o usuário cola o link (já previsto no spec).
7. **Arbeitnow**: cobertura Europa. Não serve para BR.
8. **We Work Remotely**: termos não lidos (403). Liberar só após leitura direta da página de termos e do RSS.

**Desenho concreto**

- **Adaptador por fonte** (um módulo por ATS/agregador), com a mesma saída: `fonte`, `empresa`, `titulo`, `local`, `modalidade`, `elegibilidade`, `evidencia`, `link`, `data`. Reaproveita `processar()` de `scripts/busca.py` (filtros de data, empresa excluída, título excluído e dedupe já existentes).
- **Lista de tokens** em arquivo de configuração **sem dado pessoal** (ex.: `fontes_ats.yaml`), com colunas `empresa`, `ats`, `token`, `evidencia_url` (página oficial que aponta o token) e `verificado_em`. Cada token entra só com evidência da Tabela 2.
- **Descoberta de token** (semiautomática, nunca inventada): (a) baixar a página de carreiras da empresa e procurar por `boards.greenhouse.io/<t>`, `job-boards.greenhouse.io/<t>`, `jobs.lever.co/<s>`, `jobs.ashbyhq.com/<n>`, `<s>.gupy.io`, `inhire.com.br`; (b) validar com 1 GET no endpoint público (200 e contagem); (c) confirmar que a localização das vagas bate com a empresa. Sem (a), o token não entra. Por ser lista pequena, a descoberta é feita uma vez e revisada à mão.
- **Filtro de país e remoto**: Greenhouse/Lever/Ashby pelo texto de localização e `isRemote`/`workplaceType`; Himalayas pelo parâmetro `country` e por `locationRestrictions` (vazio = worldwide; lista com Brazil = Brasil); RemoteOK e WWR pelo texto e `Anywhere in the World`. A `elegibilidade` segue as regras do `busca.md` (`brasil`, `latam`, `mundo`, `restrita`, `nao_informada`), sem supor `mundo`.
- **Deduplicação**: chave primária pelo link normalizado (sem query string); chave secundária por `empresa + titulo` normalizados. Para Himalayas, o `guid` ajuda. Quando a mesma vaga aparece no ATS e no agregador, preferir o link do ATS da empresa (fonte primária) e manter o agregador só como `fonte` secundária.
- **O que pode ser gravado em `private/vagas/`**: título, empresa, link, local, data, status, elegibilidade e a evidência curta (uma frase). Para Himalayas, RemoteOK e Remotive, incluir a atribuição de fonte no arquivo (ex.: "Fonte: Himalayas"). **Não gravar** descrição completa copiada de agregador. Os termos de Himalayas proíbem repassar a outros sites e feeds; isso cobre o uso fora do repositório. O `private/` continua sem commit e sem publicação, como já prevê o spec.
- **Cache e limites**: Himalayas (24 h) e Remotive (4 vezes por dia, no máximo 2 por minuto). Greenhouse, Lever e Ashby sem limite documentado; usar uma rodada por `/busca`, poucas requisições, com pausa de 1 a 2 s.
- **Guardrail 7**: as chamadas às APIs usam só cargo, local e regime. Nada de nome, e-mail ou dado do perfil nos parâmetros.

## Lacunas não resolvidas

- **Limites de Greenhouse, Ashby e Lever**: as páginas não informam (Greenhouse e Ashby). Lever só informa limite de POST.
- **Ashby sem chave**: a doc não diz explicitamente. A medição mostrou 200 sem chave, mas o fornecedor pode mudar. Revalidar antes de integrar.
- **Lever v0 na documentação oficial do hire.lever.co**: a página pede login. A evidência primária é o README oficial no GitHub (`lever/postings-api`); há um issue no GitHub questionando versões (v0 vs v1). Conferir antes de implementar.
- **Gupy**: não existe leitura pública sem token. Termos completos (PDF de 2024) não lidos; não há cláusula de robôs localizada. Sem parecer jurídico.
- **We Work Remotely**: termos e RSS retornaram 403; os trechos citados são de busca, não da primária.
- **RemoteOK**: limite de uso não encontrado no bloco lido.
- **Arbeitnow**: termos do site não lidos.
- **Empresas sem ATS identificado**: Mercado Livre, iFood, Itaú, Magalu, Hotmart, Zenvia, TOTVS, CloudWalk, Dock, Cora, Locaweb, Pismo, Conta Azul, Wildlife, Wellhub (página própria 403, mas token Greenhouse `gympass` existe), QuintoAndar e VTEX (páginas 404, vínculo não verificado), Stone (vínculo só pelo conteúdo). Algumas páginas retornaram 403 para este acesso, o que não prova ausência de ATS.
- **Workable, Recruitee, SmartRecruiters, InHire, Kenoby, Solides, Pandapé, Vagas.com, Catho**: não testados por API. Só InHire apareceu, em `olist.com/carreiras`.
- **Himalayas `country=Brazil`**: a semântica exata do filtro (incluir ou não vagas worldwide) é deduzida da amostra (11 de 20 com lista vazia). Confirmar com um teste de paginação antes de depender.
- **Paginação de Greenhouse e Lever**: não medida além da primeira resposta.
- **Dados de terceiros**: nada foi testado com dado pessoal; todas as consultas foram GET sem autenticação, poucas e espaçadas.
