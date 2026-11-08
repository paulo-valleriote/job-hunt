# 05: Preencher `busca.yaml` e `vagas_excluidas.md` (humano)

**What to build:** O usuário preenche com dados reais os dois arquivos de configuração, guiado pelo modelo e pelas mensagens do validador, para destravar o uso real de `/busca` e `/triagem`.

**Blocked by:** 04 (Gate de configuração)

**Status:** ready-for-human

- [ ] `vagas_excluidas.md` com cidade e regras de modalidade reais, empresas e origens a excluir
- [ ] `busca.yaml` com os critérios reais de busca
- [ ] O validador do ticket 04 passa sem apontar placeholders
- [ ] Opcional: usar a skill `wizard` para gerar um passo a passo interativo de preenchimento

**Nota:** não impede construir os tickets 06 e 07 (que usam configuração de teste); só a validação final deles com dados reais depende deste.
