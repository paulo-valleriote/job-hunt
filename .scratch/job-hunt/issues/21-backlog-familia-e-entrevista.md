# 21: backlog: família de vagas e preparação de entrevista

**What to build:** nada agora. Dois itens do upstream que decidimos **adiar**, registrados para não se perderem.

**Blocked by:** 08

**Status:** needs-triage

## A. Reaproveitar currículo de vaga parecida (`resume_matcher.py`)

O upstream varre os currículos já gerados e escolhe o de maior sobreposição de palavras-chave com a vaga nova (score = proporção das palavras-chave da vaga presentes no currículo, mínimo 0.06). É a ideia de "família de vagas" do método: versões imutáveis, uma pasta por vaga.

- Hoje só existe 1 currículo em `private/curriculos/`; com 1 não há o que comparar.
- **Reavaliar com cerca de 5 currículos.** Aí decidir entre: (a) usar o matcher só para sugerir a base; (b) deixar como está (gerar sempre do zero).
- Fecha o ponto aberto do `spec.md` ("Avaliar `resume_matcher.py` do upstream no ticket 08").

## B. `/entrevista` (preparação de entrevista)

O upstream gera `interview_prep.md` (15 perguntas, pontos a reforçar, red flags, perguntas ao entrevistador), ancorado no currículo final. O `/curriculo` não faz isso.

- Fica **fora do `/curriculo`**, para não aumentar o custo de cada execução.
- Se virar comando próprio: lê `coverage_review.md` e `profile_truth.md`; Guardrails 1 e 2 valem para o guia (sem métrica nem sistema inventado; onde não houver exemplo real, deixar `[substitua por um exemplo real seu]`).
- O método tem o prompt `06-interview-prep.md` em `vendor/`.

## Comments
