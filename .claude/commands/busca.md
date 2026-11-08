---
description: Busca 10 a 20 vagas do LinkedIn aderentes ao busca.yaml, pelo navegador (sem classificar)
---
Siga os Guardrails do CLAUDE.md. Responda em pt-BR. Método: `vendor/meu-emprego-novo/meu-emprego-novo-pipeline/docs/02-busca-de-vagas.md`.

A busca é feita **no próprio LinkedIn, pelo navegador** (Claude in Chrome, ferramentas `mcp__claude-in-chrome__*`), com os filtros da plataforma. Não use WebSearch para achar vagas: o buscador devolve páginas antigas e vagas encerradas.

1. **Gate.** Rode `make check-config`. Se falhar, mostre os problemas ao usuário e PARE.
2. **URLs.** Rode `python3 scripts/busca.py urls`. A primeira linha é `desde AAAA-MM-DD` (janela: desde a última busca). As demais são as URLs de busca, uma por cargo e local. Use exatamente essas URLs; nunca acrescente dado do perfil (Guardrail 7). Não leia nem cite `private/` no navegador.
3. **Navegador.** Carregue as ferramentas do Claude in Chrome (skill `chrome-browser`). Se a extensão não estiver conectada, diga ao usuário para conectá-la (`/chrome`) e PARE; não volte ao WebSearch. Chame `tabs_context_mcp` e abra **uma aba nova** para trabalhar.
4. **Login.** Abra a primeira URL. Se o LinkedIn pedir login, captcha ou verificação, PARE e peça ao usuário que entre ele mesmo no navegador. Nunca digite credenciais.
5. **Listagem.** Para cada URL, leia a lista de resultados (a 1ª página basta) e anote título, empresa, local, ID da vaga (`/jobs/view/<ID>`) e o tempo de publicação. Pule logo o que estiver em `private/perfil/vagas_excluidas.md` e o que for claramente outro cargo. Pare de listar quando tiver uns 25 candidatos.
6. **Verificação (uma por uma).** Abra `https://www.linkedin.com/jobs/view/<ID>/` de cada candidato e registre só o que a página mostra:
   - `data`: data de publicação em AAAA-MM-DD, convertendo "há N dias/horas" a partir de hoje. Se a página não mostrar, deixe vazio (a vaga será descartada).
   - `status`: `aberta`, ou `encerrada` se aparecer "Não aceita mais candidaturas" / "No longer accepting applications", ou `removida` se a página não existir.
   - `candidatura`: `simplificada` se o botão for "Candidatura simplificada" / "Easy Apply"; senão `externa`.
   - `local`: local e modalidade como aparecem na página.
   - `requisitos`: 1 ou 2 linhas com os requisitos principais tirados da descrição, sem completar com suposições.
   Nunca clique em candidatar, salvar ou seguir. Se a página não carregar após 2 tentativas, marque `status: removida` e siga.
7. **Gravação.** Salve todos os verificados (inclusive encerrados) como JSON, uma lista de objetos com `titulo`, `empresa`, `link` (`https://www.linkedin.com/jobs/view/<ID>/`), `local`, `data`, `status`, `candidatura` e `requisitos`, num arquivo temporário do scratchpad. Rode `python3 scripts/busca.py gravar --resultados <json>`. O script descarta vagas sem data, fora da janela, encerradas, excluídas (Guardrail 4) ou duplicadas, lista o motivo de cada descarte e grava `private/vagas/AAAA-MM-DD-busca.md` com os grupos "Candidatura simplificada" e "Candidatura externa" e numeração contínua.
8. **Fechamento.** Feche as abas que você abriu. Informe o caminho do arquivo, quantas vagas ficaram e quantas foram descartadas, por motivo. Se ficaram menos de 10, diga isso. NÃO classifique, ordene por nota nem recomende: o usuário escolhe quais triar com `/triagem` (ex.: "trie a 2 e a 5").
