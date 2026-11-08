# 10: Checagem anti-invenção

**What to build:** Todo currículo gerado é verificado, afirmação por afirmação, contra o `profile_truth.md`, de modo que qualquer fato inventado (métrica, tecnologia, cargo, certificação, data) seja apontado antes de chegar ao usuário. A checagem não pode ser desligada.

**Blocked by:** 08 (`/curriculo` básico)

**Status:** ready-for-agent

- [ ] Sempre ligada no `/curriculo`, sem opção de desativar
- [ ] Compara cada fato do currículo com o `profile_truth.md` e lista os que não têm respaldo
- [ ] Fato sem respaldo bloqueia a entrega ou vai para correção, e aparece no relatório
- [ ] Teste: uma afirmação inventada de propósito é detectada
- [ ] Teste: currículo fiel ao perfil passa sem falsos alarmes relevantes

**Nota:** compartilha o fluxo do `/curriculo` com o ticket 09; coordenar a ordem de merge se rodarem em paralelo. A última leitura do currículo continua sendo do usuário.
