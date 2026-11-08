# 06: `/busca`

**What to build:** O usuário digita `/busca` e recebe uma lista de 10 a 20 vagas do LinkedIn, aderentes ao `busca.yaml`, salva em arquivo e sem nenhuma classificação, pronta para ele escolher quais triar.

**Blocked by:** 04 (Gate de configuração)

**Status:** done

- [ ] Começa com um protótipo curto para medir a qualidade do WebSearch no LinkedIn (resultados velhos, duplicados, pouca descrição) e ajusta o desenho conforme o resultado (dica: skill `prototype`)
- [x] Recusa rodar se o validador do ticket 04 apontar placeholders
- [x] Consulta `vagas_excluidas.md` antes de buscar: nenhuma vaga excluída aparece na lista
- [x] Gera `private/vagas/AAAA-MM-DD-busca.md` com título, empresa, link, trecho e data de cada vaga, sem classificar
- [x] Remove duplicatas (testes automatizados para a deduplicação)
- [x] As consultas externas contêm só cargo, local e regime; nunca dados pessoais
- [ ] Validação final com a configuração real do usuário depende do ticket 05

## Comments

- Protótipo do WebSearch **não executado** (sem acesso à busca no ambiente do agente). O desenho já é tolerante: filtra só links do LinkedIn, descarta vagas com mais de 30 dias quando há data, aceita trecho curto e deduplica por link e por título+empresa. Ajustar `.claude/commands/busca.md` após a primeira rodada real.
- Validação final com configuração real depende do ticket 05 (humano). Pendente.
- Testes: `make test-busca`.
