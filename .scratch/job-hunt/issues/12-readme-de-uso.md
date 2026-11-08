# 12: README de uso

**What to build:** Um README curto que permite ao usuário, meses depois, reinstalar, configurar e usar o fluxo diário sem reler código.

**Blocked by:** 06 (`/busca`), 07 (`/triagem`), 09 (Avaliador + ciclo de revisão), 10 (Anti-invenção), 11 (`/enviei`)

**Status:** ready-for-agent

- [ ] Setup do zero: `make setup`, `make doctor` e a lista de pacotes LaTeX registrada no ticket 03
- [ ] O que o usuário precisa preencher e como (`busca.yaml`, `vagas_excluidas.md`)
- [ ] Fluxo diário: `/busca` → `/triagem` → `/curriculo` → envio manual → `/enviei`
- [ ] Avisos de golpes e segurança, baseados em `docs/08-golpes-e-seguranca.md` do upstream
- [ ] Aviso explícito do risco de não haver backup: `private/` é a única cópia do que for gerado
- [ ] Menciona que o envio das candidaturas é sempre manual
