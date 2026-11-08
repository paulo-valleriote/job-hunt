---
description: Currículo sob medida (PDF) para uma vaga, com relatório de cobertura
argument-hint: <link ou texto da vaga> [--en|--pt]
---
Currículo para a vaga: $ARGUMENTS

Siga os Guardrails do `CLAUDE.md`. Passos, nesta ordem:

1. **Gate.** Rode `python3 scripts/triagem.py check` e `make doctor`. Se algo falhar, mostre as mensagens e PARE.
2. **Entrada.** `python3 scripts/triagem.py entrada "<argumentos sem --en/--pt>"`. `vazio`: peça a vaga e pare. `link`: tente WebFetch; se falhar, peça o texto colado e PARE (sem WebSearch). `texto`: use como está.
3. **Idioma.** `--en`/`--pt` forçam. Senão, `python3 scripts/curriculo.py idioma "<texto da vaga>"` (heurística de stopwords; empate = EN). Se o texto for misto/curto e o resultado duvidoso, decida você e diga o motivo.
4. **Contexto (leitura).** Leia `private/perfil/profile_truth.md` (única fonte de fatos) e `private/perfil/vagas_excluidas.md`. Vaga excluída: avise e pare.
5. **Pasta.** `python3 scripts/curriculo.py pasta --empresa "<Empresa>" --cargo "<Cargo>"` (cria `private/curriculos/<data>-<empresa>-<cargo>/`).
6. **resume.json.** Leia `vendor/meu-emprego-novo/meu-emprego-novo-pipeline/prompts/04-curriculo-sob-medida.md` (se faltar, avise para rodar `make setup`) e gere `resume.json` na pasta, no idioma escolhido. Só fatos de `profile_truth.md`; nunca invente métricas, tecnologias, cargos, certificações ou datas.
7. **PDF.** `python3 scripts/curriculo.py pdf <pasta>` (valida o JSON, gera `.tex`, compila). Se falhar, corrija o JSON e repita; se for erro de LaTeX/ambiente, mostre e pare.
8. **Cobertura.** Leia `.../prompts/05-coverage-review.md` e grave `coverage_review.md` na pasta, com a seção `## Lacunas` listando o que a vaga pede e o perfil não tem. Valide: `python3 scripts/curriculo.py coverage <pasta>/coverage_review.md`.
9. **Entrega.** Mostre o caminho do PDF e as lacunas. Avise que ainda não há avaliação por nota nem checagem anti-invenção automática (tickets 09 e 10): o usuário deve ler o currículo antes de usar. Não envie nada em nome do usuário.
