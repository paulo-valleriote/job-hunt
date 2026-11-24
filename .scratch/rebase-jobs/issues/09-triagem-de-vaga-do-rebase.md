# 09: De onde o /triagem lê a descrição de uma vaga do Rebase

Type: grilling
Status: resolved
Blocked by: none
Label: wayfinder:grilling (HITL)

## Question

O registro gravado traz `link` = `apply_url` (ATS) e `atribuicao` = página do Rebase. Na triagem de uma vaga com `fonte: rebase`, de onde vem a descrição?
- (a) do `link` do ATS, como hoje;
- (b) da versão `.md` da página do Rebase (`<atribuicao>.md`, que é pública segundo a pesquisa inicial);
- (c) da API `GET /api/v1/jobs/{slug}`, com token.

Decidir também o que fazer quando a vaga já estiver encerrada (`closed_at`), e se o `scripts/triagem.py` muda.

## Answer

Decidido com o usuário em 2026-11-24. Base: `<url>.md` de duas vagas da amostra (Jobsity, Anyone AI) respondeu HTTP 200 `text/markdown` **sem token**, com o anúncio completo, empresa, localização, nível, salário (quando há) e o link de candidatura.

1. **A descrição vem da página markdown do Rebase.** Numa vaga do Rebase, o `/triagem` lê primeiro `<atribuicao>.md` via WebFetch, sem token. Se falhar, tenta o `link` do ATS. Se os dois falharem, pede que o usuário cole o texto, como hoje. Motivo: o Ashby, que é a maioria da amostra, costuma vir vazio no WebFetch. A consulta leva só a URL da vaga (Guardrail 7 ok).
2. **Vaga encerrada**: se a página disser que a vaga foi encerrada, a triagem avisa com destaque no topo e segue mesmo assim.
3. **Só instrução**: muda apenas o passo 2 de `.claude/commands/triagem.md`, que passa a dizer: "vaga com `Atribuição` do Rebase (ou link `rebasedev.com.br/jobs/…`) → leia `<url>.md` primeiro". O `scripts/triagem.py` não muda. Pode ser preciso liberar `WebFetch(domain:rebasedev.com.br)` no `.claude/settings.json`.
