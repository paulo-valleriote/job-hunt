---
description: Propõe uma empresa nova para a lista de tokens de ATS, com evidência, e acrescenta só com aprovação
argument-hint: <nome da empresa>
---
Objetivo: ampliar `fontes_ats.json` com um token de ATS **encontrado na página oficial de carreiras da empresa**. Nunca adivinhe um token a partir do nome da empresa. Empresa sem evidência fica de fora, sem erro.

Empresa: `$ARGUMENTS`. Se faltar, pergunte o nome.

Guardrail 7: toda consulta externa (busca na web, páginas, chamadas às APIs) leva só o nome da empresa, o token público do ATS e termos genéricos como "carreiras" ou "vagas". Nunca inclua dados pessoais do usuário.

Siga as etapas em ordem. Cada etapa termina numa condição de conclusão; não avance sem ela.

## 1. Pré-checagem

Leia `vagas_excluidas.md` e confirme que a empresa não está nele (Guardrail 4). Se estiver, encerre: "empresa excluída, não entra na lista".

Leia `fontes_ats.json` e confirme que a empresa não tem entrada. Se já tiver, encerre e informe o token atual.

Conclusão: a empresa não está excluída nem na lista.

## 2. Achar o ATS na página oficial

Busque `<empresa> carreiras` e abra a página de carreiras oficial da empresa (domínio da própria empresa). Procure o host do ATS na página, em links ou em scripts de incorporação:

- Greenhouse: `boards.greenhouse.io/<token>` ou `job-boards.greenhouse.io/<token>`
- Lever: `jobs.lever.co/<token>`
- Ashby: `jobs.ashbyhq.com/<token>`

O token é o trecho logo após o host. Anote a URL da página oficial onde o host apareceu; ela é a `evidencia_url`.

Se a página oficial não aponta para nenhum desses hosts, encerre: "sem evidência na página de carreiras, empresa fica de fora". Não use token deduzido de notícias, de agregadores nem do nome da empresa.

Conclusão: um par `ats` + `token` lido literalmente da página oficial, com a URL dessa página anotada.

## 3. Validar o endpoint público

Faça um GET sem chave, uma vez, no endpoint público do ATS encontrado:

- Greenhouse: `https://boards-api.greenhouse.io/v1/boards/<token>/jobs`
- Lever: `https://api.lever.co/v0/postings/<token>?mode=json`
- Ashby: `https://api.ashbyhq.com/posting-api/job-board/<token>`

Use `curl -s -o <arquivo> -w "%{http_code}"` com arquivo temporário no scratchpad. Conte as vagas da resposta.

Se a resposta não for 200, ou o JSON for inválido, encerre: "endpoint falhou (<código>), empresa fica de fora". Não repita a chamada em loop.

Conclusão: status 200, JSON válido e contagem de vagas anotada.

## 4. Conferir a localização

Nos campos de localização da resposta (por exemplo `location`, `offices`, `address`), veja se as vagas batem com a empresa, isto é, se há vaga com localização no Brasil ou na América Latina, conforme a empresa. Anote o valor literal do campo que sustentou a conferência.

Se nenhuma localização bater com a empresa, encerre: "localização não confere, empresa fica de fora".

Conclusão: uma localização literal que confere com a empresa.

## 5. Propor ao usuário e parar

Apresente a entrada proposta, sem gravar nada:

```
empresa, ats, token, evidencia_url (página oficial), verificado_em (hoje, AAAA-MM-DD), vinculo: pagina_oficial
```

Acompanhe com: quantas vagas o endpoint devolveu, a localização que conferiu e a URL da evidência.

Pergunte: "Aprova a inclusão desta empresa na lista?" Espere a resposta do usuário nesta conversa.

Conclusão: resposta explícita do usuário (sim ou não).

## 6. Gravar só com aprovação

Se o usuário disser não, encerre sem gravar.

Se o usuário aprovou explicitamente, rode, com o JSON da entrada:

```
venv/bin/python scripts/fontes.py acrescentar --json '<entrada em JSON>' --aprovado
```

O script valida a entrada (evidência https, vínculo, data, ATS, sem duplicata) e recusa o que faltar. Se sair com código diferente de 0, informe o motivo e não tente contornar a validação.

Conclusão: código 0 e a entrada aparece em `fontes_ats.json`.

## Relato

Informe em pt-BR: empresa, resultado (incluída, recusada ou fora, com o motivo), a evidência e a contagem de vagas. Não rode `/busca` nem outra coleta a partir daqui.
