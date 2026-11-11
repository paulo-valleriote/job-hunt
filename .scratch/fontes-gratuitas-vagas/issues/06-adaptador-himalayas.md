# 06: Adaptador Himalayas com atribuição e cache de 24 h

**What to build:** vagas remotas do agregador Himalayas, consultadas com `country=Brazil` e `worldwide=true` e paginação por `cursor`. Elegibilidade por `locationRestrictions`: lista vazia = `mundo`; com Brazil = `brasil`; só com outros países = `restrita`. Cada vaga traz a atribuição visível "Fonte: Himalayas" e o link de candidatura é o `applicationLink` da API. Cache de 24 h guardado em `private/` (ignorado pelo git); dentro da janela, não chama a rede. Nenhuma descrição copiada, só metadados, link, atribuição e evidência curta. Confirmar com teste de paginação a semântica real de `country=Brazil` antes de depender dela.

**Blocked by:** 02, 05

**Status:** resolved

- [ ] Lista vazia = `mundo`; com Brazil = `brasil`; só outros países = `restrita`
- [ ] Atribuição presente em toda vaga do Himalayas e visível no `render`
- [ ] Segunda chamada dentro de 24 h usa o cache e não chama a rede
- [ ] Nenhum campo de descrição copiada no arquivo gravado
- [ ] Duplicata Himalayas × ATS segue a regra do ticket 05
- [ ] Semântica de `country=Brazil` confirmada e registrada
- [ ] Testes passam em `make test-busca`, sem rede

## Comments

Implementado na branch `integration/fontes-gratuitas-vagas`.
