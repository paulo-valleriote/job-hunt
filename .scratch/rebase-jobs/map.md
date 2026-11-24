# Mapa: Rebase Jobs como fonte única de vagas (além do LinkedIn)

Label: wayfinder:map

## Destination

Uma spec com tickets `ready-for-agent` em `.scratch/rebase-jobs/` que troca as fontes por script (Greenhouse, Lever, Ashby, Himalayas, `fontes_ats.json`, `/descobrir-token`) pela API do Rebase Jobs (`https://rebasedev.com.br/api/v1`) no `/busca`. O LinkedIn, que roda pelo navegador, continua.

## Notes

- Domínio: busca de vagas (`/busca`, `scripts/busca.py`, `.claude/commands/busca.md`). Seguir os Guardrails do `CLAUDE.md` e escrever em pt-BR.
- Skills por sessão: `grilling` + `domain-modeling` nos tickets de grilling; `research` nos tickets de pesquisa.
- Decidido na abertura do mapa (2026-11-24):
  - O destino é uma spec; a implementação fica para depois.
  - A consulta vai por **script** chamando a API REST, sem MCP. Ela substitui `busca.py coletar` e mantém a saída `{vagas, falhas}`.
  - A **remoção é total**: Greenhouse, Lever, Ashby, Himalayas, `fontes_ats.json`, `fontes.py`, `/descobrir-token` e os testes deles. O histórico fica só no git.
  - O **Guardrail 7 será ampliado**: consultas externas podem levar senioridade e stack vindas do `busca.yaml`. O `minhas_skills`, que lê o perfil guardado na conta, continua proibido. A emenda entra na spec.
  - O **token** fica em `private/rebase.env`, fora do git (Guardrail 10). O usuário aceitou os termos do Rebase: e-mails de Novidades e conta via LinkedIn.
  - **Só leitura**: nada é escrito na conta do Rebase.
- Fatos-base (pesquisa de 2026-11-24, sem token):
  - O catálogo tem cerca de 670 vagas remotas de dev que aceitam quem mora no Brasil, varridas às 6h e às 18h.
  - A listagem é `GET /api/v1/jobs` com os filtros `q`/`onde=titulo`, `nivel`, `skill`, `skills_modo` e `modelo`.
  - Paginação: `por_pagina` até 50 e `pagina` até 500. Limite de 60 requisições por minuto.
  - O link de candidatura vem em `apply_url`. A autenticação é `Authorization: Bearer`.
  - Os termos permitem uso pessoal e por agentes, e proíbem republicar e compartilhar o token.

## Decisions so far

<!-- uma linha por ticket fechado -->

- [Gerar o token do Rebase e guardar em private/](issues/01-gerar-token-rebase.md): token na variável `TOKEN` de `private/rebase.env`; chamada autenticada OK (670 vagas).
- [Contrato completo da API v1 do Rebase](issues/02-contrato-da-api.md): exige token (401/403/429 tipados); sem filtro de data, então o corte é local; `url` é a página do Rebase e `apply_url` é a do ATS (pode ser nulo); requisitos vêm de `skills_principais`; `agent/jobs` evita 1+N requisições; slugs `go`/`typescript`/`nodejs`/`aws`.
- [Amostra real autenticada do catálogo](issues/03-amostra-autenticada.md): nível jr/pl + 4 skills dá 65 vagas; `q=Golang Developer` no título dá 0; filtro `nivel` some com as vagas sem seniority; `location` é texto livre; `agent/jobs` pesa ~10x; `apply_url` sempre presente na amostra.
- [Como o busca.yaml vira consulta ao Rebase](issues/04-consulta-a-partir-do-busca-yaml.md): uma consulta por stack (vinda do `stack_desejada`, validada no check-config), sem `q` e sem `nivel`; o nível é filtrado localmente (fica jr/pl/sem nível; sênior, staff e liderança são descartados); `/jobs` com teto de 10 páginas.
- [Vaga do Rebase → registro de vaga do /busca](issues/05-vaga-rebase-para-registro.md): `link` recebe `apply_url` e `atribuicao` a página do Rebase; remoto e elegível ao Brasil pela garantia do catálogo; `data` = `first_seen_at` (lê sempre as 10 páginas); requisitos de `skills_principais`; salário e modelo em `trecho`.
- [Convivência entre Rebase e LinkedIn na rodada](issues/06-convivencia-com-linkedin.md): na duplicata (empresa+título), fica a do Rebase e o LinkedIn vira secundária; o `candidatos` pula as vagas do LinkedIn que o Rebase já trouxe; o teto de 50 e o rodízio igual entre as duas fontes não mudam.
- [Falhas, token ausente e limite de taxa](issues/07-falhas-e-limites.md): sem token, o check-config barra; 401/403/rede/5xx viram falha de fonte com motivo acionável e as páginas lidas são mantidas; no 429, uma nova tentativa se o Retry-After for ≤60 s; sem cache; o doctor testa o token com 1 chamada.
- [Inventário do que sai e do que muda com a remoção](issues/08-inventario-da-remocao.md): saem coleta/himalayas/fontes, `fontes_ats.json`, `/descobrir-token`, `test_fontes` e as permissões WebFetch; mudam busca.py (coletar, _prioridade, resumo, render Trecho/Data, candidatos), test_busca, busca.md, doctor, check-config e o Guardrail 7; `ui/` não muda.
- [De onde o /triagem lê a descrição de uma vaga do Rebase](issues/09-triagem-de-vaga-do-rebase.md): primeiro `<atribuicao>.md` (pública, sem token), depois o ATS, depois o texto colado; vaga encerrada ganha aviso; muda só o `triagem.md`.

## Not yet specified

_(vazio: o caminho até a spec está livre)_


## Out of scope

- Escrever de volta no Rebase (acompanhar a vaga, etapas, ocultar) a partir do `/enviei` ou de outro comando. Foi recusado na abertura, para manter só leitura e evitar ações em nome do usuário.
- Novas fontes além do Rebase e do LinkedIn.
- Registrar o MCP do Rebase (`https://rebasedev.com.br/mcp`) para consultas avulsas fora do `/busca`: só dá para avaliar depois de usar o script na prática. Fica para um esforço futuro (decidido com o usuário em 2026-11-24).
