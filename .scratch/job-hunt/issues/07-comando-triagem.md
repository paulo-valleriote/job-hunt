# 07: `/triagem <link|texto>`

**What to build:** O usuário passa o link ou cola o texto de uma vaga e recebe uma triagem objetiva contra o seu perfil: quão aderente é, por quê, e o que falta (lacunas).

**Blocked by:** 04 (Gate de configuração)

**Status:** ready-for-agent

- [ ] Aceita link ou texto colado; se o link não abrir, pede o texto ao usuário, sem procurar a vaga em outro site
- [ ] Recusa rodar se o validador do ticket 04 apontar placeholders
- [ ] Aplica o prompt `03-triagem` do upstream com `profile_truth.md`, `busca.yaml` e exclusões
- [ ] A saída traz nota de aderência, motivos e lacunas explícitas
- [ ] Nunca cita fato que não esteja no `profile_truth.md`
- [ ] Triagem salva em `private/vagas/`
- [ ] Validação final com a configuração real do usuário depende do ticket 05
