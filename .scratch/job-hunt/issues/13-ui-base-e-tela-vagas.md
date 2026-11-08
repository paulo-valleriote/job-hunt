# 13: UI Streamlit: base + tela Vagas

**What to build:** O usuário abre uma página local, vê a lista da última busca, cola o link ou o texto de uma vaga e dispara a triagem com um clique, sem tocar no terminal.

**Blocked by:** 06 (`/busca`), 07 (`/triagem`)

**Status:** done

- [x] Streamlit servido só em `localhost`, com navegação pronta para as 3 telas (Vagas, Currículos, Tracker)
- [x] Tela **Vagas**: lista a busca mais recente e tem campo para colar link ou texto
- [x] O botão dispara o mesmo `/triagem` via `claude -p`; nenhuma lógica duplicada na UI (dica: skill `codebase-design`)
- [x] Exibe a triagem resultante (nota, motivos, lacunas)
- [x] Tudo o que a tela faz também funciona pelo comando no terminal
- [x] Visual cuidado opcional com a skill `impeccable`, se o usuário quiser
