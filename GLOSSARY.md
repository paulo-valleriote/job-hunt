# Job hunt

Assistente pessoal de busca de emprego: acha vagas aderentes ao perfil, faz a triagem e gera currículo sob medida, sem agir em nome do usuário sem aprovação.

## Language

**Fonte**:
Lugar de onde uma rodada do `/busca` tira vagas. São duas: o **Catálogo Rebase**, consultado por script, e o **LinkedIn**, consultado pelo navegador.
_Avoid_: integração, agregador, ATS

**Catálogo Rebase**:
O conjunto curado do Rebase Jobs com vagas remotas de dev em empresas de fora que contratam quem mora no Brasil.
_Avoid_: Rebase (sozinho), board

**Rodada**:
Uma execução do `/busca` que junta as fontes num arquivo do dia.
_Avoid_: varredura, coleta
