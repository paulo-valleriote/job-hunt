# 04: Adaptador Ashby

**What to build:** vagas do Ashby (token da nubank) entram pelo mesmo seam, no formato comum. A elegibilidade usa `isRemote`, `workplaceType`, `address` e `secondaryLocations` como sinal mais forte que o texto. A `evidencia` é o valor literal do campo que sustentou a decisão. Confirmar o campo de data de publicação e revalidar a leitura pública sem chave.

**Blocked by:** 02

**Status:** resolved

- [ ] Vaga com `isRemote` e endereço brasileiro é aceita
- [ ] Vaga remota sem país comprovável é descartada por elegibilidade
- [ ] Campo de data confirmado e documentado
- [ ] Erro/404 do Ashby é reportado sem derrubar a rodada
- [ ] Testes passam em `make test-busca`, sem rede

## Comments

Implementado na branch `integration/fontes-gratuitas-vagas`.
