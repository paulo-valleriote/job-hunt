# 09: Descoberta guiada de token

**What to build:** um roteiro para ampliar a lista de empresas sem adivinhar token: (a) ler a página de carreiras da empresa e procurar o host do ATS; (b) validar com um GET no endpoint público (200 e contagem); (c) conferir que as localizações batem com a empresa; (d) propor a entrada ao usuário, que aprova antes de ela entrar na lista. Sem (a), o token não entra. Empresas sem token confirmado (iFood, Mercado Livre, Itaú, Magalu e outras) seguem fora, sem erro. As consultas levam só o nome da empresa e o token público, sem dado pessoal (Guardrail 7).

**Blocked by:** 01

**Status:** resolved

- [ ] Roteiro documentado para o agente, seguindo as boas práticas de escrita para agentes
- [ ] Nenhuma entrada é gravada sem aprovação explícita do usuário
- [ ] Entrada nova traz evidência, data e tipo de vínculo, e passa pela validação do ticket 01
- [ ] Sem evidência da página de carreiras, a empresa fica de fora
- [ ] Empresa sem token confirmado não causa erro na coleta

## Comments

Implementado na branch `integration/fontes-gratuitas-vagas`.
