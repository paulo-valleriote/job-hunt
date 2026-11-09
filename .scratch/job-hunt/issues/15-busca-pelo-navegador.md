# 15: `/busca` pelo navegador, com janela de data e verificação

**What to build:** `/busca` passa a coletar vagas no próprio LinkedIn pelo navegador (no WSL2: Chromium com porta de debug + MCP `chrome-devtools`, com o login feito pelo usuário), usando os filtros da plataforma (publicada desde a última busca, regime), e verifica cada vaga antes de gravar. Substitui o WebSearch, que devolvia páginas antigas (IDs de 2022 a 2024), links 404 e vagas encerradas.

**Blocked by:** 06 (`/busca`)

**Status:** ready-for-human

Referência: `vendor/meu-emprego-novo/meu-emprego-novo-pipeline/docs/02-busca-de-vagas.md` e `prompts/02-busca-vagas.md`.

- [x] Janela incremental: "publicadas desde" = data do último `*-busca.md` (padrão 7 dias, teto 30)
- [x] `scripts/busca.py urls` gera as URLs de busca do LinkedIn com `f_TPR` e `f_WT`, contendo só cargo, local e regime
- [x] Cada vaga é aberta e verificada: data de publicação, se ainda aceita candidaturas, tipo de candidatura e requisitos principais
- [x] `gravar` descarta vaga sem data, fora da janela, encerrada, excluída ou duplicada, e lista as descartadas com o motivo
- [x] Saída no formato do original: grupos "Candidatura simplificada" e "Candidatura externa", com numeração contínua
- [x] Compatível com a tela Vagas da UI (`ui/vagas_core.py`)
- [x] Contorno do WSL2: `/chrome` (Claude in Chrome) não funciona no WSL2; `make navegador` abre o Chromium com perfil dedicado fora do repositório e `.mcp.json` registra o `chrome-devtools-mcp` (versão fixada) apontando para `127.0.0.1:9222`
- [x] URLs com `geoId` do país (Brasil, EUA, Reino Unido): o LinkedIn descarta `location=` e usava a localidade da conta
- [x] Regime remoto: `gravar` descarta vaga híbrida/presencial ou sem modalidade verificada, restrita a outro país, ou que não confirma aceitar candidatos do Brasil, LATAM ou qualquer lugar (campos `modalidade` e `elegibilidade`)
- [x] Validação humana: `/busca` rodado em 2026-11-09 com o Chromium logado no LinkedIn (14 vagas gravadas, 6 descartadas por elegibilidade)

## Comments

- O acesso por script ao endpoint público do LinkedIn foi testado e funciona, mas o classificador de permissões do Claude Code o bloqueou ao ser usado na automação. Por isso a busca é feita só pelo navegador.
- `geoId` só para países verificados no navegador. O código de "Worldwide" (92000000) não é respeitado pelo LinkedIn (devolve a localidade da conta), então ainda não há busca LATAM/mundo; falta achar um `geoId` confiável antes de incluir "LATAM" ou "Mundo" em `paises_fuso`.
- O LinkedIn acrescenta `f_SAL` (filtro de salário) sozinho à busca; origem não investigada. Pode esconder vagas sem salário informado.
- Vagas de EUA e Reino Unido quase nunca passam na elegibilidade: costumam exigir residência ou fuso do país.
