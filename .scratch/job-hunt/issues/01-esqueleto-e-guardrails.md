# 01: Esqueleto do projeto e guardrails

**What to build:** O projeto passa a existir como repositório git próprio, com proteção para que dados pessoais nunca entrem em commits, e com as regras de comportamento do assistente (guardrails) valendo para toda sessão do Claude Code aqui. Contexto geral em `../spec.md`.

**Blocked by:** None (can start immediately)

**Status:** done

- [x] `job-hunt/` tem o seu próprio `git init` (independente do repositório de `~/programming`)
- [x] `.gitignore` cobre `private/`, `vendor/`, `.env`, venv e saídas geradas
- [x] `CLAUDE.md` contém as 10 regras de guardrail do `spec.md`, mantendo a seção "Agent skills" que já existe
- [x] `git status` fica limpo e nenhum dado pessoal é rastreado
