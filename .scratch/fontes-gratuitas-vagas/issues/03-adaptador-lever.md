# 03: Adaptador Lever

**What to build:** vagas do Lever (token da neon) entram pelo mesmo seam da coleta por fontes, no formato comum e pelas mesmas regras de descarte. A elegibilidade vem do texto de localização, como no Greenhouse. Confirmar o campo de data de publicação e a paginação, e revalidar por GET que a leitura pública sem chave ainda funciona (a documentação oficial não declara isso de forma explícita).

**Blocked by:** 02

**Status:** resolved

- [ ] Resposta gravada do Lever gera vagas normalizadas, com `fonte` e `candidatura: externa`
- [ ] Elegibilidade deduzida só do texto de localização, sem `mundo` por suposição
- [ ] Campo de data e paginação confirmados e documentados
- [ ] Erro/404 do Lever é reportado sem derrubar a rodada
- [ ] Testes passam em `make test-busca`, sem rede

## Comments

Implementado na branch `integration/fontes-gratuitas-vagas`.
