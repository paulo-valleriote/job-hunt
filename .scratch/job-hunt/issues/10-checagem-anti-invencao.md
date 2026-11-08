# 10: Checagem anti-invenção

**What to build:** Todo currículo gerado é verificado, afirmação por afirmação, contra o `profile_truth.md`, de modo que qualquer fato inventado (métrica, tecnologia, cargo, certificação, data) seja apontado antes de chegar ao usuário. A checagem não pode ser desligada.

**Blocked by:** 08 (`/curriculo` básico)

**Status:** done

- [x] Sempre ligada no `/curriculo`, sem opção de desativar
- [x] Compara cada fato do currículo com o `profile_truth.md` e lista os que não têm respaldo
- [x] Fato sem respaldo bloqueia a entrega ou vai para correção, e aparece no relatório
- [x] Teste: uma afirmação inventada de propósito é detectada
- [x] Teste: currículo fiel ao perfil passa sem falsos alarmes relevantes

**Nota:** compartilha o fluxo do `/curriculo` com o ticket 09; coordenar a ordem de merge se rodarem em paralelo. A última leitura do currículo continua sendo do usuário.

**Validações humanas pendentes:** rodar `/curriculo` com perfil real e conferir se a checagem não gera falsos alarmes demais (termos próprios em PT) e se a 2ª camada (leitura do modelo) pega verbos/escopo inflados; a última leitura do currículo continua sendo sua.
