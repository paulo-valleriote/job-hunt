# Spec: fontes gratuitas de vagas no `/busca` (Greenhouse, Lever, Ashby, Himalayas)

**Status:** ready-for-agent

> Origem: pesquisa `.scratch/job-hunt/research/ats-agregadores-br.md` (consulta de 2026-11-11) e `busca-gratuita.md`, mais quatro decisões do usuário nesta sessão (ver "Decisões fechadas").
> Idioma: pt-BR; identificadores de código em inglês.
> Restrições herdadas: `.scratch/job-hunt/spec.md` (sem chave de API paga, sem auto-apply) e os guardrails do `CLAUDE.md`.

## Problem Statement

Hoje o `/busca` só coleta vagas no LinkedIn, pelo navegador. Isso deixa de fora vagas publicadas direto nas páginas de carreiras de empresas brasileiras que usam ATS abertos (Greenhouse, Lever, Ashby) e em agregadores de vagas remotas com filtro de país. Para o usuário, o resultado é uma rodada de 10 a 20 vagas que depende de uma única fonte, cuja listagem tem viés, duplicatas e vagas encerradas. Ele quer ampliar a cobertura sem pagar API, sem scraping de páginas e sem abrir mão das regras que já valem (empresas excluídas, nível acima do alvo, janela de data, elegibilidade para remoto).

## Solution

O `/busca` passa a ter uma segunda coleta, que **complementa** a do LinkedIn: um passo por script que consulta APIs públicas oficiais (GET sem chave) de empresas listadas num arquivo de tokens com evidência, mais o agregador Himalayas filtrado por Brasil e "worldwide". As vagas dessas fontes entram no mesmo fluxo de regras do `/busca` (exclusões, título de nível acima, janela, remoto, dedupe) e são gravadas no mesmo arquivo de vagas do dia, com a fonte de cada vaga e a atribuição que os termos exigem. A triagem e o currículo seguem iguais: o usuário escolhe quais triar. O envio continua sempre manual.

## User Stories

1. Como usuário, quero que o `/busca` traga também vagas direto dos sistemas de recrutamento de empresas brasileiras, para ter mais opções além das do LinkedIn.
2. Como usuário, quero que as vagas das fontes novas caiam no mesmo arquivo de vagas do dia, para triar tudo num lugar só.
3. Como usuário, quero ver em cada vaga de qual fonte ela veio, para saber onde conferir e candidatar.
4. Como usuário, quero que o fluxo do LinkedIn pelo navegador continue funcionando como hoje, para não perder as vagas que só existem lá (por exemplo, empresas em Gupy).
5. Como usuário, quero que a coleta das fontes novas rode sem navegador e sem login, para ser rápida e não gastar a cota da assinatura lendo JSON.
6. Como usuário, quero que empresas de `vagas_excluidas.md` nunca apareçam, venham de qual fonte vier, para respeitar o Guardrail 4.
7. Como usuário, quero que vagas com título de nível acima do alvo (`titulos_excluidos`) sejam descartadas também nas fontes novas, com o motivo listado, para não ver Staff, Principal ou Lead.
8. Como usuário, quero que vagas "Senior" sem outro termo excluído continuem aparecendo, para eu decidir se vale a pena.
9. Como usuário, quero que a regra de regime remoto valha igual: só passa vaga remota que aceita candidatos do Brasil, da LATAM ou de qualquer lugar.
10. Como usuário, quero que a elegibilidade das vagas dessas fontes seja deduzida só de dados estruturados da API (localização, `isRemote`, `workplaceType`, `locationRestrictions`), para nunca supor "mundo" sem base.
11. Como usuário, quero que vaga sem elegibilidade comprovável seja descartada com o motivo, em vez de entrar com chute.
12. Como usuário, quero que a mesma vaga achada no LinkedIn e no ATS da empresa apareça uma vez só, para não triar duplicata.
13. Como usuário, quero que, na duplicata, o link do ATS da empresa seja preferido ao do agregador, para candidatar pelo caminho primário (sujeito à questão aberta sobre Himalayas).
14. Como usuário, quero que o dedupe funcione por link normalizado e por empresa mais título, para pegar a mesma vaga com URLs diferentes.
15. Como usuário, quero uma lista de empresas e tokens num arquivo simples, sem dado pessoal, para saber de onde vêm as vagas e poder revisar.
16. Como usuário, quero que cada entrada da lista traga a evidência (URL oficial ou conteúdo conferido) e a data da verificação, para confiar que o token é da empresa certa.
17. Como usuário, quero que nenhum token seja inventado: só entra empresa cujo token foi validado por um GET e conferido, para evitar vagas de outra empresa.
18. Como usuário, quero que a lista já comece com os tokens testados (Greenhouse: ebanx, quintoandar, stone, gympass, vtex, inter, c6bank, rdstation; Ashby: nubank; Lever: neon), para ter valor desde a primeira rodada.
19. Como usuário, quero aprovar cada empresa nova antes de ela entrar na lista, para controlar de onde vêm as vagas.
20. Como usuário, quero um jeito guiado de descobrir o token de uma empresa (ler a página de carreiras, achar o host do ATS, validar com um GET, conferir a localização), para ampliar a lista sem adivinhar.
21. Como usuário, quero que empresas sem token confirmado (iFood, Mercado Livre, Itaú, Magalu e outras) continuem fora, sem erro, para a busca não quebrar nem inventar.
22. Como usuário, quero que as vagas do Himalayas venham de `country=Brazil` e `worldwide=true`, para cobrir remoto no Brasil e global.
23. Como usuário, quero a atribuição "Fonte: Himalayas" visível em cada vaga vinda de lá, para cumprir os termos do serviço.
24. Como usuário, quero que o Himalayas use cache de 24 h, para não bater na API sem necessidade e respeitar a atualização do serviço.
25. Como usuário, quero que nenhuma descrição completa copiada de agregador seja gravada, só metadados, link, atribuição e uma evidência curta, para respeitar os termos.
26. Como usuário, quero que a coleta use pausa de 1 a 2 s entre chamadas e uma rodada por `/busca`, para ser educado com APIs que não documentam limite.
27. Como usuário, quero que as chamadas às APIs levem só cargo, local e regime (e o token público da empresa), nunca meus dados, para cumprir o Guardrail 7.
28. Como usuário, quero que uma fonte fora do ar ou com erro não derrube a rodada: a rodada segue com as demais e avisa qual falhou, para não perder o dia.
29. Como usuário, quero que um token que passou a dar 404 seja apontado no fechamento, para eu revisar a lista.
30. Como usuário, quero que o teto de 20 vagas não seja dominado por uma fonte só, para ver variedade (rodízio entre fontes, como já é entre URLs).
31. Como usuário, quero que as vagas dos ATS apareçam no grupo "Candidatura externa", porque a candidatura é no site da empresa.
32. Como usuário, quero que a tela Vagas da UI continue lendo o arquivo gravado sem quebrar, para não perder a interface.
33. Como usuário, quero que o `/busca` informe no fechamento quantas vagas vieram de cada fonte e quantas foram descartadas por motivo, para eu entender o resultado.
34. Como usuário, quero que o `/busca` continue recusando rodar com `busca.yaml` ou `vagas_excluidas.md` incompletos, valendo também para as fontes novas.
35. Como usuário, quero que o `/busca` não grave nem comite nada de `private/` fora do lugar previsto, para cumprir o Guardrail 10.
36. Como usuário, quero que o Gupy fique fora da integração automática, e que eu possa colar o link de uma vaga Gupy na triagem como já faço, para respeitar os termos.
37. Como mantenedor, quero que cada fonte seja um adaptador que devolve o mesmo formato de vaga, para acrescentar fontes sem mexer nas regras de descarte.
38. Como mantenedor, quero testar a coleta por fontes sem rede, com respostas gravadas de cada API, para os testes serem rápidos e estáveis.
39. Como mantenedor, quero que os riscos e as lacunas da pesquisa estejam registrados na spec, para decidir com informação.

## Implementation Decisions

### Decisões fechadas com o usuário (2026-11-11)

- **Convivência:** as fontes novas **complementam** o LinkedIn pelo navegador. O `/busca` roda as duas coletas e junta o resultado num único arquivo do dia.
- **Rede:** a coleta das APIs é **por script**, com GET público sem chave, com um **fetcher injetável** para os testes. O LinkedIn segue só pelo navegador, sem script.
- **Tokens:** lista em **arquivo versionado** na raiz do projeto, sem dado pessoal. O usuário aprova cada entrada nova; o modelo propõe pela descoberta guiada.
- **Seam de teste:** um só, a coleta por fontes (ver "Testing Decisions").

### Módulos

- **Adaptadores de fonte** (Greenhouse, Lever, Ashby, Himalayas): cada um recebe a resposta crua da API e a entrada da lista de tokens e devolve vagas normalizadas. Módulo profundo: o resto do sistema não conhece o formato de cada API.
- **Coleta por fontes:** lê a lista de tokens, chama os adaptadores (via fetcher), aplica pausa, cache e tratamento de erro por fonte, e devolve a lista de vagas no formato comum, mais um relatório de falhas.
- **Regras de descarte e dedupe:** reaproveitar o `processar()` existente (exclusões, título de nível acima, status, regime remoto e elegibilidade, janela de data, duplicata, teto). As vagas das fontes novas entram nele, juntas com as do LinkedIn, para um único ponto de verdade.
- **Gravação do arquivo de vagas:** o contrato do JSON ganha `fonte` (e a atribuição quando a fonte exige). O `render` mostra a fonte em cada vaga. A validação do contrato aceita os campos novos e continua recusando chave desconhecida.
- **Comando `/busca`:** ganha um passo de coleta por fontes, antes ou depois da coleta do LinkedIn, e o fechamento passa a informar por fonte. Mudança de instrução ao agente: seguir as boas práticas de escrita para agentes.

### Formato comum de vaga

Campos: `fonte`, `empresa`, `titulo`, `local`, `modalidade`, `elegibilidade`, `evidencia`, `link`, `data`, `status`, `candidatura`, `requisitos`, mais a atribuição quando houver. Compatível com o contrato que o `gravar` já valida; valores de `modalidade`, `elegibilidade`, `candidatura` e `status` são os já existentes (`brasil`, `latam`, `mundo`, `restrita`, `nao_informada`).

- `candidatura`: `externa` para ATS (o link é do site da empresa).
- `status`: `aberta` para vaga presente na listagem pública do ATS.
- `requisitos`: pode ficar vazio nas fontes novas; não copiar descrição de agregador.

### Elegibilidade e modalidade (determinísticas, por dado estruturado)

- Greenhouse e Lever: o texto de localização é livre. Casar Brasil/cidades brasileiras com `brasil`, LATAM com `latam`, e "remoto/remote" sem país com `nao_informada` (descartada no regime remoto). Nunca supor `mundo`.
- Ashby: usar `isRemote`, `workplaceType`, `address` e `secondaryLocations` como sinal mais forte que o texto.
- Himalayas: `locationRestrictions` vazio = `mundo`; lista com Brazil = `brasil`; lista só de outros países = `restrita`.
- A `evidencia` é o valor literal do campo que sustentou a decisão.

### Lista de tokens

Colunas: `empresa`, `ats`, `token`, `evidencia_url`, `verificado_em`, e o tipo de vínculo (página oficial da empresa aponta o ATS, ou confirmado só pelo conteúdo das vagas). Só entra token com evidência; sem evidência, a empresa fica de fora. Valores iniciais: os dez tokens testados na pesquisa. Somente Ebanx e Neon têm vínculo com a página oficial verificado; os demais foram confirmados pelo conteúdo das vagas (ver Questões abertas).

### Descoberta de token (guiada, nunca inventada)

(a) ler a página de carreiras da empresa e procurar o host do ATS; (b) validar com um GET no endpoint público (200 e contagem); (c) conferir que as localizações batem com a empresa; (d) propor a entrada ao usuário, que aprova. Sem (a), o token não entra.

### Dedupe

Chave primária: link normalizado, sem query string. Chave secundária: empresa mais título normalizados. Vale entre as fontes novas e entre elas e o LinkedIn. Na duplicata, preferir o registro do ATS da empresa; o agregador fica como fonte secundária registrada.

### Gravação e atribuição

Só metadados, link, atribuição de fonte e uma evidência curta; nunca descrição completa de agregador. Himalayas exige crédito visível ("Fonte: Himalayas") e que o link de candidatura seja o `applicationLink` da API; RemoteOK e Remotive exigiriam link de volta e citação do nome. O `private/` continua sem commit e sem publicação.

### Cache, limites e rede

- Himalayas: cache de 24 h, guardado dentro de `private/` (ignorado pelo git).
- Greenhouse, Lever, Ashby: uma rodada por `/busca`, poucas requisições, pausa de 1 a 2 s.
- Falha de uma fonte (timeout, 404, 5xx, JSON inválido) é registrada e a rodada continua.
- Guardrail 7: nenhum parâmetro com dado pessoal; só cargo, local, regime e o token público.

### Ordem de integração

1. Greenhouse, Lever e Ashby, um adaptador por ATS.
2. Himalayas, com `country=Brazil` e `worldwide=true`, paginação por `cursor`, atribuição e cache.
3. RemoteOK entra depois, só se o ganho justificar (opcional, fora desta spec de entrega).

### Mudança no spec do projeto

A linha "Busca" da tabela de decisões do `spec.md` do projeto diz "Sem scraping por script". Ela deve ser ajustada para deixar claro que o proibido é raspar páginas do LinkedIn, e que GET em API pública oficial documentada, sem chave, é permitido para as fontes desta spec.

### Domínio

Termos novos para o glossário, quando houver `GLOSSARY.md` (não existe ainda; sem ADR no repositório): **fonte** (origem de vagas), **adaptador** (tradutor da API de uma fonte para o formato comum), **board token** (identificador público da empresa no ATS). Registrar via `/domain-modeling`, sem criar glossário nesta spec.

## Testing Decisions

- **O que é um bom teste aqui:** exercita o comportamento externo (o que a coleta devolve e o que o arquivo gravado contém), não funções internas nem a forma de cada parser. Sem rede, sem relógio real.
- **Seam único:** a coleta por fontes, com fetcher injetável. O teste entrega respostas gravadas de cada API (Greenhouse, Lever, Ashby, Himalayas, erro 404, resposta vazia, JSON inválido) e verifica a lista normalizada e, por cima, o resultado de `processar()` (descartes com motivo, dedupe, teto, rodízio entre fontes). Adaptadores e dedupe são cobertos só por esse seam.
- **Casos mínimos:** vaga brasileira de ATS aceita; remota sem país descartada por elegibilidade; Ashby com `isRemote` e endereço brasileiro aceita; Himalayas com lista vazia = `mundo`, com Brazil = `brasil`, só com outros países = `restrita`; mesma vaga em ATS e LinkedIn aparece uma vez, com o link do ATS; empresa em `vagas_excluidas.md` descartada; título com termo de `titulos_excluidos` descartado; fonte com erro não derruba a rodada e é reportada; token 404 reportado; Himalayas dentro das 24 h usa cache e não chama a rede; nenhum campo de descrição copiada no arquivo gravado; atribuição presente nas vagas do Himalayas; entrada de token sem evidência é recusada.
- **Contrato do gravar:** validar que `fonte` e atribuição são aceitos e que chave desconhecida continua recusada.
- **Prior art:** `tests/test_busca.py` (classes `Processar`, `Candidatos`, `Render`, `Cli`), que já usa dados em memória e chama a CLI com diretórios temporários; seguir o mesmo estilo e rodar por `make test-busca`.
- **Compatibilidade:** garantir que o arquivo gravado continua lido pela tela Vagas (`tests/test_ui_vagas.py`).

## Out of Scope

- **Gupy:** API exige token de cliente e os termos do candidato proíbem agregar. Só links colados manualmente.
- **Arbeitnow:** cobertura quase só Europa.
- **We Work Remotely:** termos não lidos (403); só reavaliar após leitura direta.
- **Remotive:** 13 vagas, nenhuma no Brasil, e os termos proíbem repassar a outros sites.
- **RemoteOK:** opcional e posterior; não faz parte da entrega.
- InHire, Workable, Recruitee, SmartRecruiters, Kenoby, Solides, Pandapé, Vagas.com, Catho: não testados.
- Empresas sem token confirmado (iFood, Mercado Livre, Itaú, Magalu, Hotmart, Zenvia, TOTVS, CloudWalk, Dock, Cora, Locaweb, Pismo, Conta Azul, Wildlife).
- Scraping de HTML de qualquer fonte, inclusive páginas Gupy com JSON-LD.
- Classificar, ordenar por nota ou recomendar vagas no `/busca` (continua do `/triagem`).
- Auto-apply, envio em nome do usuário e qualquer ação de candidatura.
- Alterar a coleta do LinkedIn, a triagem ou o currículo.
- Criar `GLOSSARY.md` ou ADR (apenas indicar os termos).

## Further Notes

### Riscos e lacunas registrados (da pesquisa; Guardrail 3)

- **Limites de uso não informados** para Greenhouse, Ashby e Lever; limite do RemoteOK não encontrado. Mitigação: uma rodada por `/busca`, pausa, poucas chamadas.
- **Ashby e Lever:** a documentação oficial não declara a leitura pública sem chave de forma explícita (funcionou por GET sem chave; a fonte do Lever é o README no GitHub, e a página de docs do hire.lever.co pede login). O fornecedor pode mudar; revalidar antes de implementar.
- **Himalayas `country=Brazil`:** a semântica exata (incluir ou não vagas "worldwide") foi deduzida de uma amostra de 20 (11 com lista vazia). Confirmar com teste de paginação antes de depender.
- **Paginação** de Greenhouse e Lever não foi medida além da primeira resposta.
- **Campos de data:** a pesquisa não mediu qual campo de cada API representa a data de publicação. Como `processar()` descarta vaga sem data verificada, o campo deve ser confirmado na implementação; se um ATS só expõe data de atualização, decidir com o usuário se ela vale.
- **Termos da Gupy e do We Work Remotely** não foram lidos integralmente; sem parecer jurídico.
- **Classificador de permissões do Claude Code:** o ticket 15 registra que o acesso por script ao LinkedIn foi bloqueado. Para as APIs oficiais pode se repetir. Saída prevista: liberar os hosts das APIs nas permissões do projeto (o usuário decide).

### Questões abertas (decidir antes ou durante a implementação)

1. **Vínculo oficial dos tokens:** a recomendação da pesquisa pede token vindo de página oficial da empresa, mas só Ebanx e Neon têm o vínculo verificado; os outros oito foram confirmados só pelo conteúdo das vagas. Sugestão: aceitar os testados, marcando o tipo de vínculo na lista, e o usuário aprova. Falta confirmar.
2. **Himalayas × dedupe:** os termos exigem que a candidatura use o `applicationLink`, e a regra de dedupe prefere o link do ATS. Se a mesma vaga existir nas duas fontes, qual link mostrar? Sugestão: preferir o ATS (uso pessoal, sem repasse), com o agregador citado como fonte secundária. Falta confirmar.
3. **Janela de data** e semântica do campo de data por ATS (ver riscos).
4. **Rodízio entre fontes** sob o teto de 20: definir a cota por fonte para o LinkedIn não ser espremido, nem o contrário.
5. **Ordem no `/busca`:** coletar as fontes novas antes ou depois do LinkedIn (afeta só o que entra primeiro no rodízio e no dedupe).

### Critérios de aceite

- [ ] `/busca` produz um único arquivo do dia com vagas do LinkedIn e das fontes novas, cada uma com `fonte`.
- [ ] Vagas das fontes novas passam pelas mesmas regras de descarte, com motivo na lista de "Descartadas".
- [ ] Empresa de `vagas_excluidas.md` e título com termo de `titulos_excluidos` nunca entram, venham de qual fonte vier.
- [ ] No regime remoto, nenhuma vaga entra sem elegibilidade comprovada por dado estruturado; nenhuma recebe `mundo` por suposição.
- [ ] A mesma vaga em duas fontes aparece uma vez, conforme a regra de dedupe.
- [ ] Token sem evidência é recusado; a lista inicial traz os dez tokens testados com evidência e data.
- [ ] Vagas do Himalayas trazem atribuição visível; nada de descrição copiada de agregador no arquivo.
- [ ] Himalayas usa cache de 24 h; as chamadas têm pausa e uma rodada por `/busca`.
- [ ] Falha ou 404 de uma fonte não derruba a rodada e é informada no fechamento.
- [ ] Nenhuma chamada externa leva dado pessoal; nada de `private/` em commit ou consulta externa.
- [ ] O fechamento informa vagas por fonte e descartes por motivo.
- [ ] Os testes do seam de coleta passam em `make test-busca`, sem rede, e a tela Vagas continua lendo o arquivo.
- [ ] O `spec.md` do projeto deixa claro que GET em API pública oficial é permitido.
