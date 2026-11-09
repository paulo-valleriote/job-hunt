# 15: `/busca` pelo navegador, com janela de data e verificação

**What to build:** `/busca` passa a coletar vagas no próprio LinkedIn pelo navegador (Claude in Chrome, com o login feito pelo usuário), usando os filtros da plataforma (publicada desde a última busca, regime), e verifica cada vaga antes de gravar. Substitui o WebSearch, que devolvia páginas antigas (IDs de 2022 a 2024), links 404 e vagas encerradas.

**Blocked by:** 06 (`/busca`)

**Status:** ready-for-human

Referência: `vendor/meu-emprego-novo/meu-emprego-novo-pipeline/docs/02-busca-de-vagas.md` e `prompts/02-busca-vagas.md`.

- [x] Janela incremental: "publicadas desde" = data do último `*-busca.md` (padrão 7 dias, teto 30)
- [x] `scripts/busca.py urls` gera as URLs de busca do LinkedIn com `f_TPR` e `f_WT`, contendo só cargo, local e regime
- [x] Cada vaga é aberta e verificada: data de publicação, se ainda aceita candidaturas, tipo de candidatura e requisitos principais
- [x] `gravar` descarta vaga sem data, fora da janela, encerrada, excluída ou duplicada, e lista as descartadas com o motivo
- [x] Saída no formato do original: grupos "Candidatura simplificada" e "Candidatura externa", com numeração contínua
- [x] Compatível com a tela Vagas da UI (`ui/vagas_core.py`)
- [ ] Validação humana: rodar `/busca` com o Chrome conectado e logado no LinkedIn

## Comments

- O acesso por script ao endpoint público do LinkedIn foi testado e funciona, mas o classificador de permissões do Claude Code o bloqueou ao ser usado na automação. Por isso a busca é feita só pelo navegador.
