# 01: Gerar o token do Rebase e guardar em private/

Type: task
Status: resolved
Blocked by: none
Label: wayfinder:task (HITL)

## Question

Com o token pessoal do Rebase Jobs disponível localmente, a API pode ser chamada pelos tickets seguintes?

Checklist do usuário (eu não faço login nem aceito termos por você):
1. Entrar em https://rebasedev.com.br/jobs com o LinkedIn.
2. Aceitar os e-mails de Novidades em https://rebasedev.com.br/jobs/perfil/aceite. Sem isso, a API responde 403.
3. Gerar o token em https://rebasedev.com.br/jobs/perfil/agentes.
4. Gravar em `private/rebase.env` uma linha `REBASE_TOKEN=<token>`. Não cole o token no chat.
5. Avisar quando estiver pronto. O agente então confere com `GET /api/v1/meta` autenticado, sem imprimir o token.

## Answer

Concluído em 2026-11-24.
- **Onde está o token**: `private/rebase.env`, na variável **`TOKEN`**, não `REBASE_TOKEN` como dizia o checklist. O script deve ler `TOKEN` desse arquivo.
- **Fora do git**: confirmado pelo `.gitignore`, que cobre `private/`.
- **Teste**: `GET /api/v1/jobs?por_pagina=1` autenticado respondeu HTTP 200, com `meta.total = 670`. Isso confirma que o aceite de Novidades está feito.
