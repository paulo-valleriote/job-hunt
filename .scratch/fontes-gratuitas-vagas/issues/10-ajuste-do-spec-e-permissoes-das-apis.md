# 10: Ajuste do spec do projeto e permissões dos hosts das APIs

**What to build:** a linha "Busca" da tabela de decisões do `spec.md` do projeto deixa claro que o proibido é raspar páginas do LinkedIn, e que GET em API pública oficial documentada, sem chave, é permitido para as fontes desta spec. Os hosts das APIs entram nas permissões do projeto, para o classificador de permissões do Claude Code não bloquear a coleta (o ticket 15 registrou bloqueio no LinkedIn); isso só é feito com a aprovação do usuário.

**Blocked by:** 02

**Status:** resolved

- [ ] `.scratch/job-hunt/spec.md` ajustado, sem afrouxar a proibição de scraping do LinkedIn
- [ ] Hosts das APIs listados ao usuário, e liberados nas permissões só com aprovação
- [ ] Nenhuma outra regra do spec do projeto alterada

## Comments

Spec do projeto ajustado; hosts liberados em `.claude/settings.json` com aprovação do usuário.
