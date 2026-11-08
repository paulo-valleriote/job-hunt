# 08: `/curriculo` básico

**What to build:** A partir de uma vaga, o usuário recebe um currículo sob medida em PDF (EN ou PT) numa pasta própria, junto com o relatório de cobertura mostrando o que a vaga pede e o perfil não tem. Ainda sem avaliação por nota nem checagem anti-invenção (tickets 09 e 10).

**Blocked by:** 03 (`make doctor` + LaTeX), 07 (`/triagem`)

**Status:** done (pendente validação humana com LaTeX real e upstream)

- [x] Fluxo completo: `resume.json` a partir do `profile_truth.md` (prompt `04`) → `.tex` (`json_para_latex.py`) → PDF com `pdflatex`
- [x] `validar_json.py` do upstream passa
- [x] Gera `coverage_review.md` (prompt `05`) listando as lacunas abertas
- [x] Idioma detectado pela vaga, com opção de forçar EN ou PT; a heurística de detecção (simples vs. delegar ao modelo) fica documentada
- [x] Saída em `private/curriculos/<data>-<empresa>-<cargo>/`
- [ ] (pendente, ver notas) Avalia se `resume_matcher.py` do upstream serve para reaproveitar o currículo mais aderente já gerado, e registra a decisão
- [ ] (pendente, ver notas) Antes de implementar, ler os docs `04`, `05` e `08` do método do upstream

## Notas da implementação
- Marcados `[x]` os critérios cobertos por código/testes com upstream e pdflatex **falsos**; a validação real fica com o humano: rodar `/curriculo` com `vendor/` e LaTeX instalados e confirmar que a CLI do upstream (`validar_json.py <json>`, `json_para_latex.py <json> <tex>`) aceita esses argumentos (assumidos, upstream não estava disponível).
- Idioma: heurística simples de stopwords EN/PT em `scripts/curriculo.py`, empate = EN; `--en`/`--pt` forçam; o modelo decide só se ambíguo.
- `resume_matcher.py`: **NÃO avaliado** (upstream ausente no ambiente). Decisão provisória: não reaproveitar neste ticket; reavaliar com `vendor/` presente.
- Pendente: ler os docs `04`, `05` e `08` do upstream (inexistentes aqui); o comando referencia os prompts 04 e 05.
