## Agent skills

### Issue tracker

Issues and specs live as local markdown files under `.scratch/<feature-slug>/`. See `docs/agents/issue-tracker.md`.

### Triage labels

Default five-role vocabulary (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: one `GLOSSARY.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`.

## Guardrails

Valem para toda sessão do Claude Code neste projeto. Responda e documente em pt-BR (identificadores de código em inglês).

1. `profile_truth.md` é a única fonte de fatos sobre o usuário; não afirmar nada que não esteja nele.
2. Nunca inventar métricas, tecnologias, cargos, certificações ou datas.
3. Se a vaga exige algo que não consta no perfil, registrar como **lacuna**.
4. Consultar `vagas_excluidas.md` antes de buscar ou recomendar vagas.
5. Nunca preencher número de documento de identidade em formulários.
6. Não enviar nada em nome do usuário sem aprovação explícita.
7. Consultas externas (WebSearch, URLs de busca no navegador) **não** podem conter dados pessoais: só cargo, local e regime.
8. Ciclo de revisão: avaliador separado de quem escreve; nota-alvo 8.5; máximo 3 revisões; parar se não melhorar; entregar a de melhor nota.
9. Checagem anti-invenção sempre ligada em `/curriculo`.
10. Nada de `private/` em commits, logs compartilhados ou consultas externas.
