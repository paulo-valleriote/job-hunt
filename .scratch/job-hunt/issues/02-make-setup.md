# 02: `make setup`

**What to build:** Um único comando deixa o ambiente pronto: baixa o upstream sem modificá-lo, cria o ambiente Python do projeto e traz os dados do usuário para dentro do projeto, sem mexer nos originais.

**Blocked by:** 01 (Esqueleto do projeto e guardrails)

**Status:** done

- [x] Clona o upstream em `vendor/meu-emprego-novo/` sem modificá-lo (ignorado pelo git)
- [x] Cria o venv do projeto (com as dependências de glue, ex.: PyMuPDF) e a pasta `private/` com a estrutura prevista no `spec.md`
- [x] Copia uma única vez perfil, PDF, tracker e `vagas_excluidas.md` de `/mnt/e/busca-vagas/privado/`; os originais ficam intactos
- [x] Roda o `checar_privacidade.sh` do upstream e mostra o resultado
- [x] Reexecutável: não sobrescreve dados já copiados e informa o que fez e o que pulou
