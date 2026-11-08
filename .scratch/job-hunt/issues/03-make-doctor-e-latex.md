# 03: `make doctor` + compilação LaTeX

**What to build:** Um diagnóstico diz se o ambiente está pronto para gerar currículos em PDF e, se não estiver, diz exatamente o que o usuário precisa rodar. O LaTeX completo passa a compilar o currículo de exemplo do upstream.

**Blocked by:** 02 (`make setup`)

**Status:** ready-for-agent

- [ ] `make doctor` verifica Python, `claude`, `pdflatex`, `private/` e placeholders nos arquivos de configuração
- [ ] O agente **não** roda `sudo`: quando falta pacote, devolve o comando exato para o usuário rodar com `! sudo apt install ...` (pacotes do TeX Live e fontes necessárias ao template, decididos após testar a compilação)
- [ ] O exemplo do upstream (`curriculo.tex` em `meu-emprego-novo-pipeline/exemplo/curriculos/dados/v1/`) compila em PDF com `pdflatex`
- [ ] A lista final de pacotes necessários fica registrada para o README (ticket 12)

**Nota:** o passo de `sudo apt install` é executado pelo usuário; o ticket fica pronto quando o PDF de exemplo compila.
