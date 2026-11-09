# 16: melhorias do `/busca` (retro do ticket 15)

**What to build:** corrigir o que a primeira rodada real do `/busca` (ticket 15) mostrou: cobertura enviesada pela primeira URL, leitura da vaga reescrita a cada página e com bugs de data, contrato do JSON sem validação, corte de vagas por julgamento, filtros do LinkedIn invisíveis e doctor cego ao navegador.

**Blocked by:** 15

**Status:** ready-for-human

- [x] `busca.py candidatos`: rodízio entre todas as URLs (máx. 5 por URL, 25 no total), sem duplicados e sem empresas excluídas
- [x] `scripts/linkedin_vaga.js`: leitura pura da vaga, testada com `node`; a data só vem do cabeçalho (nunca do card "Mais vagas")
- [x] `make doctor` avisa Chromium, `.mcp.json` e porta do navegador; o `busca.md` manda subir o navegador sozinho
- [x] `gravar --max` (padrão 20) corta por regra fixa e lista as cortadas
- [x] `gravar` recusa chave desconhecida e valor fora do enum; o arquivo mostra a `Evidência:` da elegibilidade
- [x] `busca.py filtros --url` lista filtros extras do LinkedIn (ex.: `f_SAL`); o `busca.md` manda informar
- [x] Regras de descarte em um só lugar; receita do `geoId` em `docs/agents/busca-geoid.md`
- [ ] Validação humana: rodar `/busca` de ponta a ponta com o rodízio e o `linkedin_vaga.js`

## Pendências conhecidas

- Sem guardrail automático: não há CI nem pre-commit, e `make test` roda só `tests/test_setup.sh` (as suítes Python são alvos separados). Falta um `make test-all` e um hook ou job que o chame.
- A listagem dos cartões (ID em `componentkey="job-card-component-ref-<ID>"`, cartões duplicados) ainda é um trecho JS colado à mão; só a pegadinha está documentada no `busca.md`.
- `gravar` sobrescreve o arquivo do dia sem aviso.
- Origem do filtro `f_SAL` que o LinkedIn acrescenta sozinho (agora só é reportado).
