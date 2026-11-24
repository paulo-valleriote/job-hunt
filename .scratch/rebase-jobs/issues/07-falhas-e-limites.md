# 07: Falhas, token ausente e limite de taxa

Type: grilling
Status: resolved
Blocked by: 02
Label: wayfinder:grilling (HITL)

## Question

Como o `/busca` se comporta nestes casos:
- Token ausente: falha de fonte (a rodada segue só com o LinkedIn) ou o gate `make check-config` barra?
- 401/403: token revogado ou aceite retirado.
- 429: esperar `Retry-After` ou desistir.
- Catálogo fora do ar.

Decidir também se `make doctor` passa a checar o token.

## Answer

Decidido com o usuário em 2026-11-24.

0. **Regra fixa**: o token nunca aparece em mensagem de erro, log, stderr ou arquivo gravado.
1. **Token ausente bloqueia.** Sem `private/rebase.env`, ou sem a linha `TOKEN=`, o `make check-config` falha com instrução clara ("gere o token em https://rebasedev.com.br/jobs/perfil/agentes e grave TOKEN= em private/rebase.env"), e o `/busca` para no gate.
2. **401/403 viram falha de fonte**, e a rodada segue com o LinkedIn. Os motivos são acionáveis:
   - `token recusado (401): gere outro em …/jobs/perfil/agentes`
   - `aceite de Novidades ausente (403): …/jobs/perfil/aceite`

   As páginas já lidas são mantidas, e o motivo diz em que página a leitura parou.
3. **429**: se o `Retry-After` for de até 60 s, o script espera e tenta a mesma página uma única vez. Se o 429 se repetir, ou se a espera pedida passar de 60 s, vira falha de fonte, mantendo as páginas já lidas.
4. **Rede, 5xx e JSON inválido**: falha de fonte sem nova tentativa, como hoje (`motivo_da_falha`), mantendo as páginas já lidas.
5. **Sem cache** para o Rebase. O cache em `private/cache/` sai junto com o Himalayas.
6. **`make doctor`** confere se o arquivo e o `TOKEN` existem e faz uma chamada autenticada (`GET /api/v1/jobs?por_pagina=1`). O resultado sai como `ok`, `token recusado (401)` ou `sem aceite (403)`.
