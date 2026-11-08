---
description: Busca 10 a 20 vagas do LinkedIn aderentes ao busca.yaml (sem classificar)
---
Siga os Guardrails do CLAUDE.md. Responda em pt-BR.

1. **Gate.** Rode `make check-config`. Se falhar, mostre os problemas ao usuário e PARE. Não busque nada.
2. **Consultas.** Rode `python3 scripts/busca.py queries`. Use exatamente essas linhas como consultas no WebSearch. Nunca acrescente nome, empresa anterior, salário, stack, deal-breakers ou qualquer dado do perfil (Guardrail 7). Não leia nem cite `private/` nas consultas.
3. **Coleta.** Rode as consultas no WebSearch e junte candidatos até chegar a 10 a 20 depois da deduplicação. Aceite só links de vagas do LinkedIn. Descarte vagas com mais de 30 dias quando a data aparecer. Para cada vaga, registre `titulo`, `empresa`, `link`, `trecho` (texto do resultado, sem inventar) e `data` (vazio se desconhecida). Se faltar descrição, deixe o trecho curto; não complete com suposições.
4. **Gravação.** Salve os candidatos em JSON (lista de objetos com essas chaves) num arquivo temporário e rode `python3 scripts/busca.py gravar --resultados <json>`. O script remove duplicatas e vagas de `vagas_excluidas.md` (Guardrail 4) e grava `private/vagas/AAAA-MM-DD-busca.md`.
5. **Resposta.** Informe o caminho do arquivo e a quantidade. Se vierem menos de 10, diga isso. NÃO classifique, ordene por nota nem recomende: o usuário escolhe quais triar com `/triagem`.
