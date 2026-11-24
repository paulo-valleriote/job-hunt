# 11: Falhas e limite de taxa na coleta do Rebase

**What to build:** quando a API do Rebase falha, a rodada não trava. A falha vira **falha de fonte**, com um motivo que diz o que fazer, e a rodada segue com o LinkedIn. As vagas das páginas já lidas são mantidas. O token nunca aparece em nenhuma saída.

- 401: `token recusado (401): gere outro em https://rebasedev.com.br/jobs/perfil/agentes`.
- 403: `aceite de Novidades ausente (403): https://rebasedev.com.br/jobs/perfil/aceite`.
- 429: se o `Retry-After` for de até 60 s, espera e tenta a mesma página uma única vez. Se o 429 se repetir, ou se a espera pedida passar de 60 s, vira falha de fonte.
- Erro de rede, 5xx e JSON inválido: viram falha de fonte, sem nova tentativa.
- Em qualquer falha, o motivo diz em que página a leitura parou.
- Não há cache para o Rebase.

Fonte: `.scratch/rebase-jobs/spec.md`, seção "Erros, limite de taxa e token".

**Blocked by:** 10 (Coleta do Catálogo Rebase)

**Status:** ready-for-agent

- [ ] 401 e 403 viram falha de fonte com os motivos e links da spec
- [ ] Um 429 com `Retry-After` ≤ 60 provoca uma única espera, registrada pelo `sleep` falso, e uma nova tentativa da mesma página
- [ ] Um 429 repetido, ou com espera acima de 60 s, vira falha de fonte
- [ ] Erro de rede, 5xx e JSON inválido viram falha de fonte, sem nova tentativa
- [ ] As vagas das páginas lidas antes da falha são mantidas, e o motivo cita a página em que a leitura parou
- [ ] Um teste confirma que o token não aparece em nenhum motivo, no stderr nem na saída gravada
