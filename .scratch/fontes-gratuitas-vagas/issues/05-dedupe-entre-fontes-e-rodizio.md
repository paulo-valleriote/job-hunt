# 05: Dedupe entre fontes e rodízio sob o teto de 20

**What to build:** a mesma vaga achada no LinkedIn e no ATS da empresa (ou em duas fontes novas) aparece uma vez só. Chave primária: link normalizado sem query string; secundária: empresa mais título normalizados. Na duplicata, fica o registro do ATS da empresa, e o agregador fica registrado como fonte secundária. Sob o teto de 20 vagas, o rodízio entre fontes impede que uma só domine (definir a cota por fonte, para o LinkedIn não ser espremido nem o contrário). Resolve as questões abertas 2 e 4 da spec.

**Blocked by:** 02

**Status:** resolved

- [ ] Mesma vaga em ATS e LinkedIn aparece uma vez, com o link do ATS
- [ ] Links iguais com query string diferente e empresa+título iguais com URLs diferentes são tratados como duplicata
- [ ] Rodízio entre fontes sob o teto, com cota por fonte definida e testada
- [ ] Motivo do descarte por duplicata listado em "Descartadas"
- [ ] Testes passam em `make test-busca`

## Comments

Implementado na branch `integration/fontes-gratuitas-vagas`.
