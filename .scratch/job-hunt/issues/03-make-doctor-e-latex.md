# 03: `make doctor` + compilação LaTeX

**What to build:** Um diagnóstico diz se o ambiente está pronto para gerar currículos em PDF e, se não estiver, diz exatamente o que o usuário precisa rodar. O LaTeX completo passa a compilar o currículo de exemplo do upstream.

**Blocked by:** 02 (`make setup`)

**Status:** done

- [x] `make doctor` verifica Python, `claude`, `pdflatex`, `private/` e placeholders nos arquivos de configuração
- [x] O agente **não** roda `sudo`: quando falta pacote, devolve o comando exato para o usuário rodar com `! sudo apt install ...` (pacotes do TeX Live e fontes necessárias ao template, decididos após testar a compilação)
- [x] O exemplo do upstream (`curriculo.tex` em `meu-emprego-novo-pipeline/exemplo/curriculos/dados/v1/`) compila em PDF com `pdflatex`
- [x] A lista final de pacotes necessários fica registrada para o README (ticket 12)

**Nota:** o passo de `sudo apt install` é executado pelo usuário; o ticket fica pronto quando o PDF de exemplo compila.

**Estado da implementação:** `make doctor` (`scripts/doctor.sh`) e `make test-doctor` prontos, com testes. Validado com LaTeX real (pdflatex, Ubuntu 24.04/WSL2): o `curriculo.tex` de exemplo do upstream compila em PDF (98 KB, sem erros) com a lista abaixo, sem ajustes.

**Lista final de pacotes (para o README, ticket 12):**

```
sudo apt install -y texlive-latex-recommended texlive-latex-extra texlive-fonts-recommended texlive-fonts-extra texlive-lang-portuguese lmodern
```

Falhas restantes do `make doctor` (`private/` ausente) dependem apenas de `make setup` (ticket 02) e `busca.yaml` (ticket 05).
