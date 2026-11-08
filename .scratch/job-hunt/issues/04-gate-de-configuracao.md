# 04: Gate de configuração: `busca.yaml` modelo + validador de placeholders

**What to build:** O usuário tem um modelo de critérios de busca que consegue preencher sem ler código, e existe uma verificação única que impede qualquer comando de busca ou triagem de rodar com a configuração ainda incompleta. `/busca` e `/triagem` reutilizam essa verificação.

**Blocked by:** 02 (`make setup`)

**Status:** ready-for-agent

- [ ] `busca.yaml` modelo e documentado com: cargos-alvo, senioridade, regime (remoto/híbrido), países/fuso, faixa salarial mínima, stack desejada, deal-breakers, idiomas aceitos
- [ ] Um validador único detecta placeholders ("Empresa A", "Recrutadora C", "AAAA-MM-DD", modalidade sem cidade) em `vagas_excluidas.md` e campos vazios ou de exemplo em `busca.yaml`
- [ ] Ao encontrar problema, recusa rodar com mensagem clara apontando arquivo e linha
- [ ] Testes automatizados cobrem os casos de placeholder e de configuração válida (dica: skill `tdd`)
