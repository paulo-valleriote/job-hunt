# Spec: job-hunt — assistente local de busca de vagas, triagem e currículo

> Origem: sessão de "grilling" de 2026-11-07, condensada de um HANDOFF removido em 2026-11-08.
> Idioma: o usuário trabalha em português do Brasil. Responda e documente em pt-BR (identificadores de código em inglês).
> Tickets: `issues/01..14`. Ordem e paralelismo: `flow.md`.

## Objetivo

Montar, por cima do repositório [R238Company/meu-emprego-novo](https://github.com/R238Company/meu-emprego-novo) (MIT, Python, README em pt-BR), um assistente **local** para:

1. **Buscar** vagas (10 a 20 por rodada).
2. **Triar** vagas contra o perfil do usuário.
3. **Gerar currículo sob medida** (PDF) por vaga, em EN ou PT.
4. **Registrar** candidaturas no tracker.

**O envio das candidaturas é sempre manual, feito pelo usuário.** Não há auto-apply.

## Decisões já tomadas (não reabrir sem motivo)

| Tema | Decisão |
|---|---|
| Motor | **Claude Code** com a assinatura do usuário, **sem chave de API**. Não usar o CrewAI nem o Bedrock do upstream. |
| Upstream | Clonar em `vendor/meu-emprego-novo/` **sem modificar**; ignorado pelo git do projeto. Aproveitar só `meu-emprego-novo-pipeline/prompts/`, `templates/` e `scripts/`. |
| Localização | Projeto em `~/programming/job-hunt/`, com git próprio só do código. |
| Dados | Copiar **uma vez** de `/mnt/e/busca-vagas/privado/` para `private/` (gitignored). Depois ignorar o `/mnt/e`; **não apagar nada de lá**. |
| Backup | **Nenhum.** Dados só no WSL. O usuário foi avisado: o `private/` será a única cópia do que for gerado depois. |
| PDFs | Ficam só no WSL (`private/`). Sem cópia para pastas do Windows. |
| Busca | Navegador (Chromium do WSL com porta de debug 127.0.0.1:9222 e perfil dedicado, via MCP `chrome-devtools`; o Claude in Chrome não funciona no WSL2) no LinkedIn, com login feito pelo próprio usuário e filtros de data e regime; cada vaga é aberta e verificada. 10 a 20 vagas por rodada, salvas **sem classificar**. Sem scraping por script. (Ticket 15 substituiu o WebSearch, que trazia vagas velhas e encerradas.) |
| Triagem | O usuário escolhe a vaga e envia link ou texto. **Se o link não abrir, ele cola o texto** (nada de achar a vaga em outro site). |
| Idioma do currículo | Detectado pela vaga; o usuário pode forçar. Foco em **EN**, também PT. |
| LaTeX | **Completo** (`pdflatex`). Hoje **não está instalado**; o usuário roda o `sudo apt install` com `! comando`. |
| Qualidade | Gerar → avaliar com **subagente separado** (nota 1–10) → revisar até **8.5**, no máximo **3 revisões**, parar se a revisão não melhorar, **entregar a versão de melhor nota**. Checagem **anti-invenção** contra o `profile_truth.md` sempre ligada. |
| Bloqueio | `/busca` e `/triagem` **recusam rodar** enquanto `vagas_excluidas.md` ou `busca.yaml` tiverem placeholders. |
| Tracker | CSV do upstream (`templates/tracker.csv`) é a fonte de verdade. |
| UI | **Etapa 2**, depois dos comandos estáveis. Streamlit em `localhost`; cada botão chama o mesmo comando por `claude -p` (headless, CLI oficial). |
| Fora de escopo | Auto-apply e envio em nome do usuário; scraping direto do LinkedIn; login no LinkedIn pela ferramenta; CrewAI/Bedrock/APIs pagas; edição do perfil do LinkedIn. |

## Guardrails (vão para o `CLAUDE.md` no ticket 01)

Regras do usuário (copiar como estão):

1. `profile_truth.md` é a única fonte de fatos sobre ele; não afirmar nada que não esteja nele.
2. Nunca inventar métricas, tecnologias, cargos, certificações ou datas.
3. Se a vaga exige algo que não consta no perfil, registrar como **lacuna**.
4. Consultar `vagas_excluidas.md` antes de buscar ou recomendar vagas.
5. Nunca preencher número de documento de identidade em formulários.
6. Não enviar nada em nome do usuário sem aprovação explícita.

Regras novas:

7. Consultas externas (WebSearch, URLs de busca no navegador) **não** podem conter dados pessoais: só cargo, local e regime.
8. Ciclo de revisão: avaliador separado de quem escreve; nota-alvo 8.5; máximo 3 revisões; parar se não melhorar; entregar a de melhor nota.
9. Checagem anti-invenção sempre ligada em `/curriculo`.
10. Nada de `private/` em commits, logs compartilhados ou consultas externas.

## Fatos verificados

**Upstream** (243 estrelas, último push 2026-11-03):

- A CLI (CrewAI, `main.py`) **só** gera currículo. **Não busca nem tria vagas**; isso só existe como prompts (`02-busca-vagas.md`, `03-triagem.md`).
- O LLM entra por `src/llm_factory.py` e os agentes usam tool calling, por isso o CrewAI não roda bem sem API. Foi o motivo de escolher o Claude Code como motor.
- Prompts úteis em `meu-emprego-novo-pipeline/prompts/`: `01-perfil-mestre`, `02-busca-vagas`, `03-triagem`, `04-curriculo-sob-medida`, `04b-ajustar-curriculo`, `05-coverage-review`, `06-interview-prep`, `07-resumo-tracker`, `09-linkedin`, `10-retrospectiva`.
- Scripts úteis em `meu-emprego-novo-pipeline/scripts/`: `json_para_latex.py`, `validar_json.py`, `checar_privacidade.sh`.
- Templates em `meu-emprego-novo-pipeline/templates/`: `profile_truth.md`, `resume.json`, `tracker.csv`, `vagas_excluidas.md`.
- Docs de método em `meu-emprego-novo-pipeline/docs/00..10-*.md`. Ler `04`, `05` e `08` antes de implementar.
- `src/scripts/resume_matcher.py` (extrai título de cargo da vaga e acha o currículo mais aderente já gerado) pode ser reaproveitado; não foi lido por inteiro.

**Ambiente do usuário** (WSL2, Linux):

- `python3.12` e `claude` (`~/.local/bin/claude`) presentes.
- `pdflatex` **ausente**. `PyMuPDF` não instalado no Python do sistema (usar venv do projeto).
- `codex` e `agy` não estão no PATH do WSL; não são necessários.
- `~/programming` é um repositório git de outros projetos; `job-hunt/` deve ter o seu **próprio** `git init`.

**Dados existentes do usuário** (só caminhos; **não copiar conteúdo para o repositório**):

- `/mnt/e/busca-vagas/privado/perfil/profile_truth.md`: 173 linhas, **já no formato do template do upstream**; não precisa de conversão.
- `/mnt/e/busca-vagas/privado/perfil/resume.pdf`: currículo atual (idêntico ao PDF em Downloads do Windows).
- `/mnt/e/busca-vagas/privado/perfil/tracker.csv`: só o cabeçalho (`data,empresa,vaga,fonte,tipo,link,curriculo,status,proximo_passo,observacoes`).
- `/mnt/e/busca-vagas/privado/perfil/vagas_excluidas.md`: **ainda é o modelo**, com placeholders ("Empresa A", "Recrutadora C", "AAAA-MM-DD", modalidade sem cidade).
- `/mnt/e/busca-vagas/AGENTS.md`: as 6 regras do usuário acima.
- `/mnt/e/busca-vagas` **não é** um repositório git.

## Estrutura alvo

```
~/programming/job-hunt/
├── CLAUDE.md                   # guardrails
├── Makefile                    # setup, doctor
├── .gitignore                  # private/, vendor/, .env, outputs, venv
├── vendor/meu-emprego-novo/    # clone do upstream (ignorado)
├── .claude/commands/           # /busca /triagem /curriculo /enviei
├── .claude/agents/             # avaliador de currículo (subagente)
├── busca.yaml                  # critérios (modelo; usuário preenche)
├── scripts/                    # glue em Python/bash (venv próprio)
├── ui/                         # Streamlit (etapa 2)
└── private/                    # dados do usuário (ignorado pelo git)
    ├── perfil/                 # profile_truth.md, resume.pdf, vagas_excluidas.md
    ├── vagas/                  # AAAA-MM-DD-busca.md, triagens
    ├── curriculos/<data>-<empresa>-<cargo>/   # json, tex, pdf, coverage_review.md, rating_report.md
    └── tracker.csv
```

## Estimativa e riscos

- Sem UI: cerca de 3 a 5 dias; com UI: 5 a 7 dias.
- Riscos: (1) WebSearch no LinkedIn devolve resultados irregulares, velhos ou duplicados, com pouca descrição, e por isso a triagem exige texto colado; (2) cota da assinatura gasta pelo ciclo de revisão (se apertar, reduzir o teto de 3 para 1 revisão); (3) invenção em currículos nunca é zerada, e a última leitura é do usuário.

## Pontos abertos

- O usuário precisa preencher `vagas_excluidas.md` e `busca.yaml` antes do primeiro uso real (ticket 05).
- Como detectar o idioma da vaga (heurística simples vs. delegar ao modelo): escolha livre do implementador no ticket 08; documentar.
- Nome exato dos pacotes do TeX Live: decidir depois de testar a compilação do template (ticket 03).
- Avaliar `resume_matcher.py` do upstream no ticket 08.
- Confirmar com o usuário se `/mnt/e/busca-vagas` pode ser movido/arquivado depois da cópia (hoje: só ignorar).

## Skills úteis

`mattpocock-skills:tdd` (validador, dedup, escrita no CSV), `diagnosing-bugs` (LaTeX ou `claude -p` intermitente), `codebase-design` (camada de comandos fina, UI sem lógica duplicada), `prototype` (qualidade do WebSearch no ticket 06), `wizard` (passos que só o usuário executa: `sudo apt`, preencher configs), `code-review` (ao fim do M2), `impeccable` (visual do Streamlit, se o usuário quiser).
