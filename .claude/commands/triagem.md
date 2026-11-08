---
description: Triagem de uma vaga (link ou texto colado) contra o perfil
argument-hint: <link ou texto da vaga>
---
Triagem da vaga: $ARGUMENTS

Siga os Guardrails do `CLAUDE.md`. Passos, nesta ordem:

1. **Gate.** Rode `python3 scripts/triagem.py check`. Se sair com erro, mostre as mensagens, diga para preencher `busca.yaml`/`vagas_excluidas.md` (ver `busca.example.yaml`) e PARE. Não faça mais nada.
2. **Entrada.** Rode `python3 scripts/triagem.py entrada "<argumentos>"`.
   - `vazio`: peça o link ou o texto da vaga e pare.
   - `link`: tente abrir com WebFetch. Se não abrir ou vier sem descrição útil, peça ao usuário que cole o texto da vaga e PARE. Não procure a vaga em outro site nem via WebSearch.
   - `texto`: use como está.
3. **Contexto (apenas leitura).** Leia `private/perfil/profile_truth.md`, `busca.yaml` e `private/perfil/vagas_excluidas.md`. Se a vaga/empresa constar em `vagas_excluidas.md` ou bater com um `deal_breakers`, diga isso com destaque.
4. **Prompt do upstream.** Leia `vendor/meu-emprego-novo/meu-emprego-novo-pipeline/prompts/03-triagem.md` (se faltar, avise para rodar `make setup`) e aplique-o à vaga, com os três arquivos acima.
5. **Regras de conteúdo.** Só cite fatos do usuário que estejam em `profile_truth.md`. Nunca invente métricas, tecnologias, cargos, certificações ou datas. Tudo que a vaga exige e não consta no perfil vai em **Lacunas**. Nenhuma consulta externa com dados pessoais.
6. **Formato da saída** (markdown):
   ```
   # Triagem: <Empresa>, <Cargo>
   Nota de aderência: N/10
   ## Motivos
   - ...
   ## Lacunas
   - ... (ou "Nenhuma lacuna identificada.")
   ```
7. **Salvar.** Grave a saída num arquivo temporário e rode `python3 scripts/triagem.py salvar <arquivo> --empresa "<Empresa>" --cargo "<Cargo>"`. O arquivo vai para `private/vagas/`. Se o validador reclamar, corrija a saída e repita. Mostre a triagem e o caminho ao usuário.

Não envie nada em nome do usuário.
