# 08: `/curriculo` básico

**What to build:** A partir de uma vaga, o usuário recebe um currículo sob medida em PDF (EN ou PT) numa pasta própria, junto com o relatório de cobertura mostrando o que a vaga pede e o perfil não tem. Ainda sem avaliação por nota nem checagem anti-invenção (tickets 09 e 10).

**Blocked by:** 03 (`make doctor` + LaTeX), 07 (`/triagem`)

**Status:** ready-for-agent

- [ ] Fluxo completo: `resume.json` a partir do `profile_truth.md` (prompt `04`) → `.tex` (`json_para_latex.py`) → PDF com `pdflatex`
- [ ] `validar_json.py` do upstream passa
- [ ] Gera `coverage_review.md` (prompt `05`) listando as lacunas abertas
- [ ] Idioma detectado pela vaga, com opção de forçar EN ou PT; a heurística de detecção (simples vs. delegar ao modelo) fica documentada
- [ ] Saída em `private/curriculos/<data>-<empresa>-<cargo>/`
- [ ] Avalia se `resume_matcher.py` do upstream serve para reaproveitar o currículo mais aderente já gerado, e registra a decisão
- [ ] Antes de implementar, ler os docs `04`, `05` e `08` do método do upstream
