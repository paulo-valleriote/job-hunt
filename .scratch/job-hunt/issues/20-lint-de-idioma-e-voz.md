# 20: lint de idioma e voz do currículo

**What to build:** o upstream proíbe misturar idiomas (currículo em PT sem frase em inglês) e exige verbos em 1ª pessoa no passado. Nosso prompt de currículo não diz nada disso e a heurística de idioma só olha a vaga. Criar um lint que **avisa**, sem bloquear.

**Blocked by:** 08

**Status:** ready-for-agent

- [x] `curriculo.py lint <pasta> --idioma en|pt`: para cada texto livre do `resume.json` (resumo, destaques), conta stopwords EN × PT e avisa o campo que destoa do idioma escolhido
- [x] Avisa destaque que começa com verbo em 3ª pessoa ("Desenvolveu", "Developed" é 1ª pessoa implícita e passa; critério fixado nos testes)
- [x] Saída: lista de avisos em stdout, exit 0 sempre (não bloqueia); falso positivo é esperado com siglas e nomes de tecnologia, que são ignorados
- [x] Teste primeiro (`mattpocock-skills:tdd`): currículo PT com um destaque em inglês → 1 aviso; currículo coerente → nenhum aviso; campo curto só com siglas → nenhum aviso
- [x] `.claude/commands/curriculo.md`: rodar o lint depois do passo 7 e mostrar os avisos na entrega (passo 9)
- [x] Reaproveitar as listas `EN`/`PT` de `curriculo.py` em vez de duplicar

## Notas

- Por que só aviso: heurística de stopwords erra em texto curto.
- A voz (1ª pessoa, passado) é convenção do upstream; se o resultado real mostrar que não serve para nós, descartar o critério da 3ª pessoa e ficar só no idioma.
