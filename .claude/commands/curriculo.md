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
8b. **Avaliação e revisão (Guardrail 8).** Salve o `resume.json` atual como `versoes/v1/resume.json`. Depois, em laço:
   a. Dispare um **subagente avaliador** (Agent), separado de quem escreveu, passando só `vaga`, `profile_truth.md` e o `resume.json` da versão. Ele responde JSON puro: `{"nota": 1-10, "pontos_fortes": [], "lacunas": [], "palavras_chave": []}`; grave em `versoes/vN/avaliacao.json` e valide com `python3 scripts/avaliador.py validar <arquivo>`.
   b. `python3 scripts/avaliador.py decidir <pasta>`. Se `revisar`: leia `.../prompts/04b-ajustar-curriculo.md` e gere `versoes/v(N+1)/resume.json` (anexos: versão atual, `profile_truth.md`, vaga, `coverage_review.md`; sem cobrir lacunas), volte ao passo a.
   c. Se `parar: <motivo>`: `python3 scripts/avaliador.py finalizar <pasta>` (copia a versão de **melhor nota**, não a última, para `resume.json` e grava `rating_report.md`), e então repita o passo 7 (`curriculo.py pdf`).
   Alvo 8.5, máx. 3 revisões (reduza com `JOBHUNT_MAX_REVISOES=1` se a cota apertar).
9. **Entrega.** Mostre o caminho do PDF e as lacunas. Mostre o histórico de notas (`rating_report.md`) e qual versão foi entregue. Ainda não há checagem anti-invenção automática (ticket 10): o usuário deve ler o currículo antes de usar. Não envie nada em nome do usuário.
