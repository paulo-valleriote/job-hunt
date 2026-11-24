# 08: Inventário do que sai e do que muda com a remoção

Type: task
Status: resolved
Blocked by: none
Label: wayfinder:task (AFK)

## Question

Que arquivos, funções, testes, alvos do Makefile, documentos e trechos de comando dependem das fontes removidas (`coleta.py`, `himalayas.py`, `fontes.py`, `fontes_ats.json`, `/descobrir-token`, cache do Himalayas)? Para cada um: sai, muda (e o quê) ou fica. Inclui `busca.py` (`coletar_todas`, `_fonte_de`, `_prioridade`, "Tokens com 404"), `.claude/commands/busca.md`, `.claude/settings.json` (hosts liberados), README, `ui/`, a spec `fontes-gratuitas-vagas` e o vendor de método. Só produzir o inventário, sem apagar nada.

## Answer

Inventário feito em 2026-11-24 por `grep` no repo, sem `venv/`, `private/`, `.git` e `.scratch`. Nada foi apagado.

### Sai
- `scripts/coleta.py` (Greenhouse, Lever, Ashby; `elegibilidade_do_local`, `modalidade_do_local`, `motivo_da_falha`, `http_get`). **Atenção**: `motivo_da_falha` e `http_get` são reaproveitáveis. Mover para o novo módulo do Rebase em vez de perder.
- `scripts/himalayas.py`, junto com o cache em `private/cache/himalayas.json`. O arquivo local é apagado à mão, fora do git.
- `scripts/fontes.py` e `fontes_ats.json`.
- `.claude/commands/descobrir-token.md`.
- `tests/test_fontes.py` inteiro.
- `.claude/settings.json`: as 4 permissões `WebFetch(domain:…)` (greenhouse, lever, ashby, himalayas). Avaliar se entra `rebasedev.com.br`; o script usa urllib, não WebFetch, então provavelmente não precisa.

### Muda
- **`scripts/busca.py`**:
  - **Imports e cabeçalho**: saem os imports de `coleta`, `himalayas` e `fontes` (`ARQUIVO`, `ATS`, `carregar_fontes`), e o docstring do cabeçalho (linhas 4–9) precisa ser reescrito.
  - **`coletar`**: o comando lê do Rebase e o argumento `--fontes` sai. `coletar_todas` é substituída pela coleta do Rebase.
  - **`_prioridade`**: prioridade 0 passa a ser `fonte == "rebase"` (ticket "Convivência entre Rebase e LinkedIn na rodada"). Comentários e docstrings de `_fonte_de`, `_prioridade`, `_rodizio` e `processar` citam ATS/Himalayas e precisam ser atualizados.
  - **`resumo`**: a seção "# Tokens com 404" sai, porque não há mais tokens.
  - **`render`**: a linha `- Trecho:` mostra `requisitos or trecho`, e o requisito esconde o trecho. Com a decisão do ticket "Vaga do Rebase → registro de vaga do /busca" (requisitos em `requisitos`, salário e modelo em `trecho`), o `render` precisa mostrar os dois. `- Data:` precisa dizer "entrou no Rebase em" nas vagas do Rebase.
  - **`candidatos`**: ganha `--coletadas` para pular as vagas do LinkedIn que o Rebase já trouxe (ticket "Convivência entre Rebase e LinkedIn na rodada").
- **`tests/test_busca.py`**:
  - Saem os imports de `coleta`/`himalayas` (linhas 12–13) e a classe `FontesAts` (cerca da linha 481).
  - Os testes de dedupe e rodízio (cerca das linhas 187–260 e 519–524) usam `fonte="greenhouse:…"`, `lever`, `himalayas`. Reescrever com `fonte="rebase"`, mantendo os mesmos comportamentos.
  - Os testes do adaptador Rebase entram novos.
- **`.claude/commands/busca.md`**:
  - Descrição e passo 2: "fontes de ATS e agregador" passa a ser "Rebase".
  - Passo 6: `candidatos` com `--coletadas`.
  - Passo 9: sai "Tokens com 404 / revisão de fontes_ats.json".
- **`scripts/doctor.sh`**: checagem do token com 1 chamada (ticket "Falhas, token ausente e limite de taxa").
- **`scripts/validar_config.py`** (`make check-config`): checagem de `private/rebase.env`/`TOKEN` e validação de `stack_desejada` contra as skills do `/api/v1/meta` (tickets 04 e 07).
- **`CLAUDE.md`**: emenda do Guardrail 7 (senioridade e stack do `busca.yaml` podem ir em consulta externa; `minhas_skills` proibido).
- **`GLOSSARY.md`**: já atualizado na abertura do mapa.

### Fica (sem mudança)
- **`ui/`**: `ui/vagas_core.py` lê do arquivo do dia só `empresa`, `link`, `data` e `trecho`. Nenhuma tela depende das fontes removidas. Se o `render` mudar o rótulo `- Data:` ou o `- Trecho:`, o parser por chave continua funcionando, desde que as chaves `Data`/`Trecho` sejam mantidas.
- **`scripts/enviei.py`**: `--fonte` é texto livre. Passa a receber `rebase` sem mudar código.
- **`scripts/triagem.py`**, `Makefile` (não tem alvo de fontes; `test-busca` segue), `tests/test_ui_vagas.py`.
- **`.scratch/fontes-gratuitas-vagas/`**: histórico da spec anterior. Fica como registro. A nova spec cita que a substitui.
- **`vendor/`**: nenhuma referência às fontes removidas.
