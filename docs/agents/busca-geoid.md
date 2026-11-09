# geoId do LinkedIn no `/busca`

O LinkedIn descarta `location=` na URL e usa a localidade da conta; só o `geoId` fixa o local. Os códigos vivem em `GEO_IDS` (`scripts/busca.py`).

| Local | geoId | Estado |
|---|---|---|
| Brasil | 106057199 | verificado |
| EUA | 103644278 | verificado |
| Reino Unido | 101165590 | verificado |
| América Latina | 91000011 | verificado |
| Worldwide | 92000000 | **inútil**: a lista é a mesma de não passar `geoId` (padrão da conta, com viés para a América Latina); a palavra `worldwide` no termo também não muda |
| Europa, Oriente Médio e África | 91000007 | verificado, mas não é nenhum dos locais da busca |

## Acrescentar um local

1. **Achar o código.** Em `https://www.linkedin.com/jobs/`, os links de "Pesquisas de vagas recentes" trazem o `geoId` do local usado (leia o `url=` do link; é como se achou o da América Latina). Local sem pesquisa recente: peça ao usuário para pesquisá-lo uma vez na interface, porque o `/busca` não digita em formulários.
2. **Confirmar.** Abra `https://www.linkedin.com/jobs/search/?keywords=Backend+Developer&geoId=<ID>&f_TPR=r172800&f_WT=2&sortBy=DD` e conte os países dos 25 cartões. Vale se a lista for do local e diferente da busca sem `geoId`. O LinkedIn mantém o `geoId` na URL final mesmo quando não o honra, então a URL não prova nada.
3. **Registrar.** Acrescente o nome em inglês (o de `LOCAIS`) e o código em `GEO_IDS`, um teste em `tests/test_busca.py` (classe `Urls`) e uma linha na tabela acima.
