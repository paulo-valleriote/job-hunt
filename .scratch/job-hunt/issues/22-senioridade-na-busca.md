# 22: senioridade na busca: filtrar por título antes de verificar

**What to build:** hoje a busca não olha o nível da vaga, então chegam muitas vagas senior para um perfil pleno. Fazer o `/busca` descartar por título as vagas de nível claramente acima, sem esconder as "Senior" que podem ter bom match.

**Blocked by:** nenhum

**Status:** needs-triage

## O que foi observado

- `scripts/busca.py urls` monta as URLs só com `keywords`, `geoId`, `f_TPR`, `f_WT` e `sortBy`. Nenhum campo de nível entra.
- `senioridade`, `stack_desejada` e `deal_breakers` do `busca.yaml` só são validados (não vazios) em `validar_config.py`. Quem os lê é o `/triagem`, como contexto.
- A nota de aderência sai do `/triagem` (vaga × `profile_truth.md`), não do `busca.yaml`.

## Opções

- **A. Campo novo `titulos_excluidos`** (ex.: Staff, Principal, Lead, Head, Director). `processar()` descarta pelo título, com motivo na lista de "Descartadas". Fica de fora "Senior", para o usuário ainda ver essas vagas e decidir. Preferida: corta antes de gastar a verificação (uma página por vaga).
- **B. Filtro `f_E` do LinkedIn** (2 Entry, 3 Associate, 4 Mid-Senior). Corta só Director e Executive, porque vaga "senior" costuma estar em Mid-Senior. Ganho pequeno, e `f_E` teria de entrar em `PARAMS_ESPERADOS` (hoje seria avisado como filtro extra).
- **C. `NOT Senior` nas keywords.** Descartaria também as mid-senior com bom match, o que o usuário quer manter. Não recomendada.

## Critérios de aceite

- [ ] Com `titulos_excluidos` preenchido, vaga cujo título contém um dos termos (sem acento, sem diferença de caixa, palavra inteira) vai para "Descartadas" com o motivo.
- [ ] Vaga "Senior" sem outro termo da lista continua aceita.
- [ ] Campo ausente ou vazio não muda o comportamento atual.
- [ ] Teste em `make test-busca` cobrindo os três casos acima.
- [ ] `busca.example.yaml` e o README explicam o campo.

## Comments
