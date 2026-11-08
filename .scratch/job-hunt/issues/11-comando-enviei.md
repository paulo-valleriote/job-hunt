# 11: `/enviei <vaga>`

**What to build:** Depois de enviar a candidatura manualmente, o usuário registra com um comando e a vaga entra no tracker com o currículo que foi usado.

**Blocked by:** 02 (`make setup`)

**Status:** done

- [x] Acrescenta uma linha ao `private/tracker.csv` respeitando o cabeçalho existente (`data,empresa,vaga,fonte,tipo,link,curriculo,status,proximo_passo,observacoes`)
- [x] Aponta o currículo usado, quando existir um gerado para a vaga
- [x] Não duplica linhas ao registrar a mesma vaga duas vezes
- [x] O CSV continua abrindo normalmente no Excel
- [x] Testes automatizados para escrita e deduplicação (dica: skill `tdd`)
- [x] Nunca envia nada em nome do usuário: só registra
