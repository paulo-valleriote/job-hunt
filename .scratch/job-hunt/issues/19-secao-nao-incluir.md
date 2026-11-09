# 19: seção `Termos proibidos` no perfil, checada pelo `anti_invencao.py`

**What to build:** o upstream põe no perfil uma seção "NÃO INCLUIR" com o que nunca pode aparecer no currículo. O nosso perfil já diz o que não pode ser afirmado (o avaliador citou que o perfil "proíbe afirmar RabbitMQ"), mas só o prompt respeita isso. Criar a seção e fazer a checagem reprovar se algum termo aparecer no `resume.json`.

**Blocked by:** 10

**Status:** ready-for-human

- [x] Perfil real: a seção `Não Incluir` (regras em prosa) já existia, como H1; virou `## Não Incluir` (mesmo texto) e ganhou `## Termos proibidos` com RabbitMQ, smart contract(s) e contrato(s) inteligente(s), por autorização do usuário. SAGA ficou de fora (regra condicional: "sem evidência concreta") e mTLS também (regra de contexto); ambos seguem na 2ª camada (leitura do `/curriculo`)
- [x] `templates/profile_truth.md` (ou o modelo local usado pelo `make setup`) ganha a seção com um exemplo comentado. Se o modelo vier do upstream em `vendor/`, o ajuste vai no nosso modelo, não no upstream
- [x] `anti_invencao.py checar` lê `## Termos proibidos` e reprova (exit 1) se algum termo aparecer em qualquer texto do `resume.json`; comparação normalizada (acento, caixa), por palavra inteira
- [x] Seção ausente ou vazia: aviso no `anti_invencao.md`, sem bloquear
- [x] Resultado em seção própria "Termos proibidos" no `anti_invencao.md`
- [x] Teste primeiro (`mattpocock-skills:tdd`): termo presente → exit 1; ausente → exit 0; palavra contida em outra (ex.: "Go" em "Google") não reprova
- [x] `.claude/commands/curriculo.md` (passo 7b) menciona a checagem

## Notas

- Os termos da seção não podem vazar para `coverage_review.md` nem para logs compartilhados (Guardrail 10).
- Compartilha arquivos com o ticket 18; fazer 18 antes para não conflitar.

- Efeito colateral útil: a camada de invenção aceita "RabbitMQ" no currículo porque a palavra aparece no perfil (nas regras de "não afirmar"); a lista de termos proibidos fecha essa brecha.
