# 06: `/busca`

**What to build:** O usuário digita `/busca` e recebe uma lista de 10 a 20 vagas do LinkedIn, aderentes ao `busca.yaml`, salva em arquivo e sem nenhuma classificação, pronta para ele escolher quais triar.

**Blocked by:** 04 (Gate de configuração)

**Status:** ready-for-agent

- [ ] Começa com um protótipo curto para medir a qualidade do WebSearch no LinkedIn (resultados velhos, duplicados, pouca descrição) e ajusta o desenho conforme o resultado (dica: skill `prototype`)
- [ ] Recusa rodar se o validador do ticket 04 apontar placeholders
- [ ] Consulta `vagas_excluidas.md` antes de buscar: nenhuma vaga excluída aparece na lista
- [ ] Gera `private/vagas/AAAA-MM-DD-busca.md` com título, empresa, link, trecho e data de cada vaga, sem classificar
- [ ] Remove duplicatas (testes automatizados para a deduplicação)
- [ ] As consultas externas contêm só cargo, local e regime; nunca dados pessoais
- [ ] Validação final com a configuração real do usuário depende do ticket 05
