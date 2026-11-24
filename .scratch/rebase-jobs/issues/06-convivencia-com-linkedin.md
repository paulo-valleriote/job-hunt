# 06: Convivência entre Rebase e LinkedIn na rodada

Type: grilling
Status: resolved
Blocked by: 05
Label: wayfinder:grilling (HITL)

## Question

Na rodada que junta Rebase e LinkedIn: qual é a ordem e o rodízio, como fica o teto de 50 gravadas, e como tirar duplicadas quando a mesma vaga aparece nas duas fontes com links diferentes (empresa + título normalizados? `tambem_publicada`?).

## Answer

Decidido com o usuário em 2026-11-24.

1. **Na duplicata, fica a vaga do Rebase.** O Rebase herda a prioridade 0 que hoje é do ATS direto (`_prioridade`). O LinkedIn fica em `fontes_secundarias`, inclusive quando a vaga dele é de candidatura simplificada. A duplicata só é detectada pela chave empresa+título normalizados, já que link e empresa nunca coincidem entre as fontes. A dedupe continua em `processar()`.
2. **Não verificar no navegador o que o Rebase já trouxe.** O `busca.py candidatos` passa a receber também o JSON coletado do Rebase (ex.: `--coletadas <scratchpad>/fontes.json`). Uma vaga da listagem do LinkedIn com a mesma empresa+título de uma vaga do Rebase sai antes da verificação, com o motivo "já veio do Rebase" no stderr. O `/busca` relata esses cortes no fechamento. Isso só é possível porque a coleta do Rebase vem antes.
3. **O teto e o rodízio não mudam.** São 50 vagas, com rodízio igual entre `rebase` e `linkedin` e a sobra de uma fonte indo para a outra. A ordem segue a mesma: primeiro o Rebase, depois o LinkedIn.
