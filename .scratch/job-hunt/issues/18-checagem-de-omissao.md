# 18: checagem de omissão no `anti_invencao.py`

**What to build:** hoje a checagem só pega o que foi **inventado**. Nada garante, de forma determinística, que todo empregador, cargo, período, formação e certificação do `profile_truth.md` esteja no `resume.json`; a seção "Preservado" do `coverage_review.md` é só texto do modelo. O upstream exige o mesmo número de empregos da fonte. Acrescentar um bloco "omissões" à checagem.

**Blocked by:** 10

**Status:** ready-for-human

- [x] `anti_invencao.py checar` lê do perfil as experiências (`### Empresa — Cargo (datas)`), a formação e as certificações, e reprova (exit 1) se algum item não estiver no `resume.json`
- [x] O resultado entra em `anti_invencao.md` numa seção própria "Omissões", separada de "Sem respaldo"
- [x] Tolerância a EN×PT já existente (glossário, números, status de certificação) vale para a comparação
- [x] Teste primeiro (`mattpocock-skills:tdd`): perfil mínimo + `resume.json` sem uma empresa → exit 1; completo → exit 0; formação/certificação faltando → exit 1
- [x] Perfil sem a estrutura esperada: erro de uso claro (exit 2), sem passar em silêncio
- [x] `.claude/commands/curriculo.md` (passo 7b) menciona que omissão também bloqueia a entrega
- [x] Docstring do módulo atualizada (o "Limite" passa a dizer o que a checagem cobre)

## Notas

- O perfil é privado (`private/`); os testes usam perfil fictício (Guardrail 10).
- Omissão por relevância não existe: o upstream mantém todas as posições, mesmo as pouco ligadas à vaga, para não criar lacuna falsa no histórico. A diferença para nós é o limite de bullets por recência (ver nota de decisão no `spec.md`).
