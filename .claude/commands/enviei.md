---
description: Registra no tracker uma candidatura que o usuário já enviou manualmente
argument-hint: <empresa> | <vaga> [| link]
---
O usuário JÁ enviou a candidatura manualmente. Apenas registre; **nunca envie nada** em nome dele (Guardrail 6).

Entrada: `$ARGUMENTS` (empresa, vaga e, opcionalmente, fonte/link). Se faltar empresa ou vaga, pergunte.

Rode (preenchendo só o que o usuário informou; não invente fonte, link nem tipo):

```
venv/bin/python scripts/enviei.py --empresa "<empresa>" --vaga "<vaga>" [--fonte ..] [--tipo ..] [--link ..]
```

O script acrescenta uma linha a `private/tracker.csv`, aponta o currículo gerado em `private/curriculos/` quando existir e não duplica a vaga. Informe o resultado em pt-BR. Não exiba o conteúdo de `private/`.
