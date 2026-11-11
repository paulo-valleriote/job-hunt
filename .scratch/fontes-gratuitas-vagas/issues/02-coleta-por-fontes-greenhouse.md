# 02: Coleta por fontes com Greenhouse (tracer bullet)

**What to build:** um passo por script que lê a lista de tokens, consulta a API pública do Greenhouse (GET sem chave) por um fetcher injetável e devolve vagas no formato comum. As vagas entram em `processar()` junto com as demais e passam pelas mesmas regras (empresa excluída, título de nível acima, status, regime remoto, janela de data, duplicata, teto), com motivo na lista de "Descartadas". A elegibilidade vem só do texto de localização: Brasil/cidades brasileiras = `brasil`, LATAM = `latam`, "remoto" sem país = `nao_informada`; nunca `mundo` por suposição. `candidatura` é `externa`, `status` é `aberta`, `requisitos` pode ficar vazio. Pausa de 1 a 2 s entre chamadas, uma rodada por `/busca`. Falha de uma fonte (timeout, 404, 5xx, JSON inválido) é registrada e a rodada continua. As chamadas levam só o token público (Guardrail 7). Confirmar qual campo do Greenhouse representa a data de publicação; se só houver data de atualização, decidir com o usuário se ela vale.

**Blocked by:** 01

**Status:** resolved

- [ ] Seam único: a coleta com fetcher injetável, testada sem rede com respostas gravadas (sucesso, 404, vazia, JSON inválido)
- [ ] Vaga brasileira de ATS é aceita; remota sem país é descartada por elegibilidade
- [ ] Empresa de `vagas_excluidas.md` e título com termo de `titulos_excluidos` são descartados
- [ ] Fonte com erro ou token 404 não derruba a rodada e entra no relatório de falhas
- [ ] O campo de data usado está documentado e validado, ou a dúvida foi levada ao usuário
- [ ] Nenhuma descrição completa é gravada; `fonte` presente em cada vaga
- [ ] Testes passam em `make test-busca`

## Comments

Implementado na branch `integration/fontes-gratuitas-vagas`.
