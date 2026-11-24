# 15: Remoção das fontes antigas

**What to build:** o repositório deixa de ter as fontes antigas (Greenhouse, Lever, Ashby, Himalayas), e as instruções e permissões passam a refletir as fontes reais: o **Catálogo Rebase** e o **LinkedIn**. O histórico fica no git.

- Saem: o módulo de coleta de ATS, o módulo do Himalayas, o módulo de fontes, `fontes_ats.json`, o comando `/descobrir-token`, os testes de fontes e as classes de teste de ATS e do Himalayas dentro dos testes do `busca`.
- `busca.py`: sai o argumento `--fontes`, sai a seção "# Tokens com 404" do `resumo`, e os imports e docstrings que citam ATS, Himalayas e tokens são reescritos.
- `.claude/settings.json`: saem as quatro permissões `WebFetch(domain:…)` de greenhouse, lever, ashby e himalayas.
- `.claude/commands/busca.md`: a descrição e o passo 2 falam em Rebase, e o passo 9 perde "Tokens com 404 / revisão de fontes_ats.json".
- Ficam sem mudança: `ui/`, `scripts/enviei.py`, `scripts/triagem.py`, o `Makefile`, `vendor/` e a pasta `.scratch/fontes-gratuitas-vagas/`.
- O cache `private/cache/himalayas.json` é apagado à mão, fora do git. Basta lembrar o usuário no fechamento do ticket.

Fonte: `.scratch/rebase-jobs/spec.md`, seção "Remoção" e histórias 41–46.

**Blocked by:** 10 (Coleta do Catálogo Rebase), 11 (Falhas e limite de taxa), 14 (LinkedIn pula vagas do Rebase; também edita o `busca.md`)

**Status:** resolved

- [x] Os módulos de coleta de ATS, do Himalayas e de fontes, `fontes_ats.json`, `/descobrir-token` e `test_fontes` não existem mais
- [x] Nenhum import, docstring ou comentário restante cita Greenhouse, Lever, Ashby, Himalayas ou `fontes_ats.json`, exceto no histórico em `.scratch/`
- [x] `--fontes` sai do `coletar`, e o `resumo` não tem mais a seção "Tokens com 404"
- [x] O `settings.json` não tem mais as permissões de WebFetch dos quatro hosts removidos
- [x] O `busca.md` descreve a coleta por script como Rebase e não cita mais `fontes_ats.json`
- [x] `make test-busca`, `make test-config`, `make test-doctor` e `make test-ui` passam
