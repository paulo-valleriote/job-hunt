# 12: Checagem de config e `doctor` para o Rebase

**What to build:** o usuário descobre antes da rodada se o token e a stack estão certos.

- `make check-config`:
  - falha se `private/rebase.env` ou a linha `TOKEN=` não existirem, com a mensagem "gere o token em https://rebasedev.com.br/jobs/perfil/agentes e grave TOKEN= em private/rebase.env";
  - valida o `stack_desejada` traduzido contra a lista de skills do `GET /api/v1/meta`. Uma stack desconhecida falha com uma mensagem clara que cita o termo.
- `make doctor`: confere o arquivo e o `TOKEN` e faz uma única chamada `GET /api/v1/jobs?por_pagina=1`. A saída é `ok`, `token recusado (401)` ou `sem aceite (403)`.
- Nenhum campo novo no `busca.yaml`, e o `busca.example.yaml` não muda de forma.

Fonte: `.scratch/rebase-jobs/spec.md`, seção "Configuração e diagnóstico".

**Blocked by:** 10 (Coleta do Catálogo Rebase: leitura do token e tradução da stack)

**Status:** ready-for-agent

- [ ] `make check-config` falha com a instrução da spec quando o arquivo ou a linha `TOKEN=` faltam
- [ ] `make check-config` falha com uma mensagem clara quando uma stack não existe no `/meta`, e passa com apelidos como "Golang" e "Node.js"
- [ ] Os testes do validador injetam a lista do `/meta`, sem rede
- [ ] `make doctor` informa `ok`, `token recusado (401)` ou `sem aceite (403)`, com uma única chamada
- [ ] O teste em shell do doctor usa uma API falsa que devolve 200, 401 ou 403
- [ ] O token não aparece na saída do check-config nem na do doctor
