# Busca de vagas de graça: opções verificadas

- Data da consulta: 2026-11-11
- Escopo: fontes gratuitas e de uso permitido para complementar o `/busca` (hoje só LinkedIn, pelo navegador).
- Restrições do spec respeitadas: sem API paga, sem auto-apply, sem scraping do LinkedIn por script, navegador só lê.
- Consultas externas: só cargo, local e regime. Nenhum dado pessoal foi usado.
- Marcação: "não verificado" = não confirmado na fonte primária. Nada de endpoint, limite ou preço inventado.

## Resumo executivo

Recomendação em ordem:

1. **APIs públicas de ATS das empresas-alvo (Greenhouse e Ashby)**: são as fontes mais limpas. Leitura sem autenticação, documentadas pelo fornecedor, e trazem a vaga direto da empresa (candidatura externa, que o usuário faz manualmente). Custo: esforço de montar uma lista de empresas-alvo que usam esses ATS. Cobertura de Brasil/LATAM **não verificada**.
2. **Agregadores de vagas remotas com API gratuita (Remotive, Himalayas, RemoteOK)**: são gratuitos e documentados, mas exigem atribuição (link de volta e citação da fonte) e têm restrições de reuso. Cobrem vagas remotas globais; cobertura específica de Brasil/LATAM é **não verificada** e precisa filtro por elegibilidade (campo `elegibilidade`, já previsto no `/busca`).
3. **Repositório da comunidade `frontendbr/vagas` (GitHub)**: licença MIT, vagas em issues com cidade no título. Útil para vagas brasileiras, mas o conteúdo é voluntário, sem garantia de atualização, e a leitura automatizada dos dados precisa de um cuidado de validação.
4. **Melhorias de pipeline sem custo** (independentes de fonte): deduplicação entre fontes, mais URLs de cargo/sinônimos no LinkedIn, e paginação. Paginação via `start=` **não verificada** em fonte primária.

Não recomendo, até verificação: scraping de portais de vagas que não publicam API (LinkedIn, Indeed, Gupy sem documentação de leitura confirmada), e fontes cujos termos proíbam reenvio para terceiros sem confirmar o uso pretendido.

## Tabela comparativa

| Opção | Custo | Cobertura BR/LATAM/remoto | Limites de uso | Termos e atribuição | Esforço | Compatível com o spec |
|---|---|---|---|---|---|---|
| Greenhouse Job Board API | Gratuito (leitura GET sem token) | Depende das empresas escolhidas. BR/LATAM **não verificado** | Não encontrado na doc consultada (**não verificado**) | Dados públicos; sem termos de atribuição encontrados na página lida | Baixo-médio: uma chamada por empresa (`board_token`) | Sim (API pública documentada, sem scraping) |
| Ashby Public Job Posting API | Gratuito (endpoint GET público descrito) | Depende das empresas. BR/LATAM **não verificado** | Não informado na página (**não verificado**) | Não lido; a página não diz se exige autenticação de forma explícita | Baixo-médio: uma chamada por empresa (nome do job board) | Sim, com a ressalva de confirmar a ausência de autenticação |
| Remotive API | Gratuito | Remoto global; LATAM/Brasil **não verificado** | Máx. 4 req./dia recomendado; mais de 2 por minuto é bloqueado | Link de volta à URL do Remotive + citar Remotive como fonte; sem reenvio a terceiros; vagas com atraso de 24 h | Baixo: JSON com filtros `search`, `category`, `limit` | Sim (API de terceiro, sem scraping) |
| Himalayas API | Gratuito ("The API is free to use") | Remoto, com filtro `country` e `worldwide`; BR **não verificado** | Sem chave: pool público compartilhado; com chave gratuita: 60/min e 10.000/dia por conta | Link visível ao Himalayas; candidatura obrigatoriamente pelo `applicationLink`; não repassar a agregadores nem ao LinkedIn Jobs; cache de 24 h | Baixo-médio | Sim; o `applicationLink` é compatível com candidatura manual |
| RemoteOK API | Gratuito (condições de uso lidas) | Remoto global; BR **não verificado** | Não confirmado (**não verificado**) | Link de volta "with follow" e citação do Remote OK; marca não pode ser usada sem permissão escrita | Baixo | Sim, com atribuição |
| We Work Remotely (RSS) | Gratuito (feed RSS público) | Remoto global; BR **não verificado** | Não verificado | Termos de reuso **não verificados** | Baixo (RSS) | Provável, mas condição de uso a confirmar antes de integrar |
| Arbeitnow Job Board API | Não verificado | Amostra majoritariamente Alemanha; BR não cobre | Não verificado | Licença não verificada | Não verificado | Não verificado |
| Lever postings API | Não verificado | Não verificado | Não verificado | Não verificado | Não verificado | Não verificado (página de documentação retornou 404) |
| Gupy (API pública) | Não verificado | Gupy é ATS muito usado no Brasil; cobertura **não verificada** | Não verificado | Autenticação e termos **não verificados** (só há índice da doc) | Não verificado | Não verificado; só integrar após confirmar leitura sem chave |
| GitHub `frontendbr/vagas` (via REST API) | Gratuito. Sem token: 60 req./h por IP; com token pessoal: 5.000 req./h | Vagas brasileiras (FrontendBR); foco em front-end | Limites acima | Licença MIT; vagas enviadas como issues, com cidade entre colchetes | Médio (parsing de issues) | Sim (API de primeira parte) |
| LinkedIn: alertas de vaga por e-mail | Gratuito | Mesma cobertura do LinkedIn | Não verificado | Página de ajuda retornou 404 (**não verificado**) | Baixo, mas não alimenta o projeto automaticamente | Sim, como complemento manual |
| LinkedIn: filtros extras na URL (`f_E`, `f_JT`, `sortBy`, `start=`) | Gratuito | Mesma cobertura | Não verificado | Termos da LinkedIn proíbem bots e coleta por script (ver riscos) | Baixo | Sim, como navegação manual |
| Google for Jobs / JobPosting | Gratuito, mas é marcação para quem **publica**, não para consumo | N/A para consumo | N/A | Doc de publisher | N/A | Não serve para buscar vagas |

## Detalhes por opção

### 1. Greenhouse Job Board API

- Leitura pública, sem autenticação: "Job Board data is publicly available, so authentication is not required for any GET endpoints." Fonte: https://docs.greenhouse.io/job-board.html (a URL `developers.greenhouse.io` redireciona para essa).
- Endpoint: `GET https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs`, com `content=true` opcional para descrição completa. Fonte: mesma URL.
- Apenas a candidatura (POST) exige Basic Auth. Fonte: mesma URL.
- Limite de requisições: a página lida não menciona. **Não verificado.**
- Cobertura: depende de quais empresas usam Greenhouse e têm `board_token`. **Não verificado** para empresas brasileiras.
- Integração: lista de empresas-alvo em arquivo de configuração (sem dado pessoal), uma chamada GET por empresa, depois o mesmo `processar()` do `busca.py`.

### 2. Ashby Public Job Posting API

- Endpoint: `GET https://api.ashbyhq.com/posting-api/job-board/{JOB_BOARD_NAME}?includeCompensation=...`. Fonte: https://developers.ashbyhq.com/docs/public-job-posting-api
- Vagas com `isListed` falso "should only be available via direct link". Mesma fonte.
- A página não afirma explicitamente que não há autenticação, e não informa limite. **Não verificado** nesses dois pontos.

### 3. Remotive API

- Endpoint: `https://remotive.com/api/remote-jobs`, com `category`, `company_name`, `search` e `limit`. Fonte: https://github.com/remotive-io/remote-jobs-api (a URL `remotive.com/api-documentation` redireciona para esse repositório).
- Limite: "we advise max. 4 times a day"; "excessive requests (more than 2x per minute) will be blocked". Mesma fonte.
- Atribuição: "link back to the URL found on Remotive AND mention Remotive as a source". Mesma fonte.
- Proibido: "do not submit Remotive jobs to third Party websites" (cita Google Jobs e LinkedIn Jobs). Mesma fonte.
- Atraso: "Jobs displayed are delayed by 24 hours". Mesma fonte.
- Cobertura Brasil/LATAM: **não verificado**.

### 4. Himalayas API

- Endpoints: feed em `https://himalayas.app/jobs/api`, busca em `https://himalayas.app/jobs/api/search` (com `q`, `country`, `worldwide`, `timezone`, `seniority`, `page`), verificação de vaga aberta em `.../companies/:company/jobs/:slug`. Fonte: https://himalayas.app/docs/remote-jobs-api
- Gratuito: "The API is free to use." Mesma fonte.
- Limites: sem chave, "share one public allowance with every other caller"; com chave, "60 requests per minute and 10,000 per UTC day for the account". Mesma fonte.
- Cache de 24 h: "refreshed every 24 hours". Mesma fonte.
- Candidatura: "must use the API's applicationLink, not a direct employer/ATS link". Mesma fonte.
- Restrição: "Do not pass them on to other job boards, aggregators, Google Jobs or LinkedIn Jobs". Mesma fonte.
- Atribuição: "Display visible Himalayas source credit." Mesma fonte.

### 5. RemoteOK API

- Endpoint: `https://remoteok.com/api` (retorna JSON; primeiro item traz `legal`). Fonte: https://remoteok.com/api
- Atribuição: link de volta "with follow" e citação do Remote OK; logo não pode ser usado sem permissão por escrito. Mesma fonte.
- Limites: não encontrados na parte lida (**não verificado**). A página tem mais de 600 mil caracteres e só o início foi lido.

### 6. We Work Remotely (RSS)

- Feed: `https://weworkremotely.com/remote-jobs.rss` (RSS 2.0, canal "We Work Remotely"). Fonte: a própria URL. Categorias vistas: DevOps and Sysadmin, Management and Finance, Full-Stack Programming, Sales and Marketing, Customer Support.
- Termos de reuso: **não verificado** (não encontrados no trecho lido).

### 7. Arbeitnow

- A página lida era a de listagem, não de documentação. Endpoint, paginação, limites e licença: **não verificado**. Amostra com vagas predominantemente na Alemanha.

### 8. Lever

- As URLs de documentação consultadas retornaram 404. Existência e condições do endpoint público: **não verificado**.

### 9. Gupy

- Há índice de documentação em https://developers.gupy.io/ com "Listing jobs" em "Gupy Public API > Jobs", sem método nem caminho mostrados.
- Autenticação e "Rate-Limiting" aparecem no índice, mas sem conteúdo lido. Se a leitura é sem chave e quais são os termos: **não verificado**.
- Relevância: Gupy é ATS usado por muitas empresas brasileiras; vale confirmar antes de decidir.

### 10. GitHub: `frontendbr/vagas`

- Licença MIT; vagas são enviadas abrindo uma issue com a cidade entre colchetes (exemplo: `[São Paulo] Front-End Developer na [NOME DA EMPRESA]`), com labels de nível e tipo de contratação. Fonte: https://github.com/frontendbr/vagas
- Há modelo de issue (`.github/ISSUE_TEMPLATE/adicionar-nova-vaga.md`); vagas fora do modelo podem ser removidas. Mesma fonte.
- Não há arquivo consolidado; os dados estão nas issues. Mesma fonte.
- Acesso: API REST do GitHub. Sem token, 60 req./h por IP; com token pessoal, 5.000 req./h. Fonte: https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api
- Endpoint de issues (`GET /repos/{owner}/{repo}/issues`) é o padrão da API e **não foi lido na doc** nesta consulta; confirmar antes de implementar.
- Ressalva: a licença do repositório é MIT, mas o **conteúdo das vagas** é de terceiros (quem posta). Não verificado se há termos específicos sobre reuso dos dados.

### 11. LinkedIn: alertas, filtros e termos

- Alertas de vaga: página de ajuda consultada retornou 404. Frequência e canais: **não verificado**.
- Robots: as regras visíveis para Googlebot não bloqueiam `/jobs/view/<id>` em geral; bloqueiam `/jobs?runSearch*`, `/jobs/view/externalApply/`, `/jobs-guest/` e `/api/jobPostings/jobs*`. O bloco `User-agent: *` não foi lido (truncado). Fonte: https://www.linkedin.com/robots.txt
- Termos (vigência 3 de novembro de 2025), seção 8.2: proíbe "Develop, support or use software, devices, scripts, robots or any other means or processes" para acessar ou copiar dados (item 2); "Use bots or other unauthorized automated methods" (item 13); "Override any security feature or bypass or circumvent any access controls" (item 3); "Copy, use, display or distribute any information (including content) obtained from the Services" (item 4). Fonte: https://www.linkedin.com/legal/user-agreement
- Consequência: o spec já proíbe scraping por script; o uso atual (navegador, leitura manual) é o que o spec adotou. Filtros de URL manual são navegação e não violam os termos por si. Paginação via `start=`: **não verificado** em fonte primária.

### 12. Google for Jobs / JobPosting

- Propriedades obrigatórias: `datePosted`, `description`, `hiringOrganization`, `jobLocation`, `title`. Fonte: https://developers.google.com/search/docs/appearance/structured-data/job-posting
- A marcação é para quem **publica** vagas em páginas individuais ("must only be used on pages that contain a single job posting"). Não há uso de consumo gratuito documentado nesta fonte. Mesma fonte.
- Se o usuário quiser "buscar pelo Google", o caminho é busca comum, o que o spec já descartou (WebSearch, ticket 15). Não recomendado.

## Riscos e lacunas

- **Cobertura BR/LATAM**: a maioria das APIs de agregadores é global ou de remoto genérico. Nenhuma fonte foi confirmada com cobertura brasileira, exceto o repositório `frontendbr/vagas` (voluntário e focado em front-end).
- **Atribuição e reenvio**: Remotive, Himalayas e RemoteOK exigem link de volta e citação. Um relatório local e pessoal provavelmente não exibe a vaga a terceiros, mas os termos não dizem isso de forma explícita; confirmar com o usuário antes de qualquer publicação.
- **Atraso de dados**: Remotive (24 h) e Himalayas (24 h de cache) atrasam a informação; a verificação de "aberta" continua necessária, como no fluxo atual.
- **Termos do LinkedIn**: o fluxo atual (leitura pelo navegador, cada vaga verificada) fica no limite dos termos, que proíbem "scripts, robots" e cópia de conteúdo. O spec já proíbe scraping por script; isso precisa ser lembrado ao expandir. Não é parecer jurídico.
- **Lacunas não verificadas**: limites do Arbeitnow, Lever, Gupy, WWR e RemoteOK; cobertura BR de quase tudo; endpoint de issues do GitHub; alertas do LinkedIn; paginação do LinkedIn.
- **Dados pessoais**: nenhuma consulta externa incluiu dados do usuário. Ao integrar, as chamadas às APIs devem usar só cargo, local e regime (Guardrail 7).
- **Qualidade**: como visto no `/busca`, vagas de fonte externa também precisam de verificação (data, status e elegibilidade) antes de entrar no arquivo final. Os campos de `processar()` servem para isso sem mudança.

## Próximos passos sugeridos (sem implementar)

1. Pedir ao usuário uma lista curta de empresas-alvo (nome e se usam Greenhouse ou Ashby) e confirmar a leitura sem autenticação de Ashby e a cota de Greenhouse, lendo a doc com mais profundidade.
2. Testar manualmente, uma vez, os endpoints de Remotive e Himalayas com `search` por cargo, para medir volume e campos reais (sem dados pessoais), antes de decidir.
3. Confirmar os termos de reuso de We Work Remotely e RemoteOK (página de termos completa) e os limites do RemoteOK.
4. Confirmar a leitura pública da Gupy (página de Authentication e Rate-Limiting) e, se for sem chave, avaliar como fonte BR.
5. Avaliar o `frontendbr/vagas` como fonte BR complementar, após confirmar o endpoint de issues na doc da REST API do GitHub.
6. Se for integrar, adicionar um campo `fonte` às vagas (ex.: `linkedin`, `greenhouse`, `himalayas`) e manter o dedupe por link normalizado e por empresa+título, já presente em `processar()`.
7. Manter a regra do spec: nenhuma consulta com dado pessoal e nenhum envio em nome do usuário.
