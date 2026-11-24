# 05: Vaga do Rebase → registro de vaga do /busca

Type: grilling
Status: resolved
Blocked by: 02, 03
Label: wayfinder:grilling (HITL)

## Question

Como cada campo do registro gravado pelo `busca.py gravar` (`titulo`, `empresa`, `link`, `local`, `modalidade`, `elegibilidade`, `evidencia`, `data`, `status`, `candidatura`, `requisitos`, `fonte`) é preenchido a partir da vaga do Rebase?
- O `link` aponta para `apply_url` ou para a página do Rebase?
- A `elegibilidade` passa a ser `brasil` por definição do catálogo? Qual texto vai na `evidencia`?
- A `data` usa `published_at` ou `first_seen_at`? A API não filtra por data, então o corte da janela "desde a última busca" é local. Com `published_at`, a paginação para na primeira vaga anterior à janela; com `first_seen_at`, ela lê até o teto de 10 páginas (ver o ticket "Como o busca.yaml vira consulta ao Rebase").
- Os `requisitos` vêm de `skills_principais` ou da descrição?
- A vaga ganha `fonte: "rebase"`. Precisa de atribuição, segundo os termos?

## Answer

Decidido com o usuário em 2026-11-24. Cada vaga do Rebase vira um registro do `gravar` assim:

| Campo | Valor |
|---|---|
| `titulo` | `title` |
| `empresa` | `company.name` |
| `link` | `apply_url` (candidatura oficial no ATS). Vaga sem `apply_url` é descartada com motivo. |
| `atribuicao` | `url` (página da vaga no Rebase, que tem a descrição) |
| `local` | `location`, literal |
| `modalidade` | `remoto` (garantia do catálogo: `remoto_comprovado`) |
| `elegibilidade` | `brasil` (garantia do catálogo: `hires_in_brazil`) |
| `evidencia` | `Rebase: contrata quem mora no Brasil (<location>)` |
| `data` | data (AAAA-MM-DD) de **`first_seen_at`**, a entrada no catálogo. A janela "desde a última busca" corta por ela. |
| `requisitos` | `Requer: ` + `skills_principais` separados por vírgula; vazio se a lista vier vazia |
| `trecho` | modelo de contratação e salário, quando houver (ex.: `PJ · USD 5000–7000/mês`); vazio se não houver |
| `status` | `aberta` (o catálogo só lista vagas abertas) |
| `candidatura` | `externa` |
| `fonte` | `rebase` |

Consequências:
- Como `first_seen_at` não segue a ordem da listagem, a leitura do ticket "Como o busca.yaml vira consulta ao Rebase" vai **sempre até o teto de 10 páginas**, sem parada antecipada.
- A data mostrada no arquivo do dia passa a significar "entrou no Rebase em". O `render` deve deixar isso claro nas vagas do Rebase.
- O contrato não exige atribuição. Usamos `atribuicao` para guardar a página do Rebase, não por obrigação.
