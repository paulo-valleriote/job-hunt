#!/usr/bin/env bash
# Diagnostica se o ambiente gera currículos em PDF. Nunca roda sudo:
# imprime o comando exato para o usuário executar com `! sudo apt install ...`.
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT" || exit 1
# Pacotes TeX Live do template do upstream (lista confirmada: o exemplo compila com ela).
APT_PKGS="texlive-latex-recommended texlive-latex-extra texlive-fonts-recommended texlive-fonts-extra texlive-lang-portuguese lmodern"
EXAMPLE_DIR=vendor/meu-emprego-novo/meu-emprego-novo-pipeline/exemplo/curriculos/dados/v1
BAD=0
good() { echo "ok    - $1"; }
bad()  { echo "FALTA - $1"; BAD=1; }
hint() { echo "        -> $1"; }

if command -v python3 >/dev/null; then good "python3 ($(python3 --version 2>&1))"
else bad "python3 ausente"; hint "! sudo apt install python3 python3-venv"; fi

if command -v claude >/dev/null; then good "claude (CLI)"
else bad "claude CLI ausente"; hint "instale o Claude Code: https://claude.com/claude-code"; fi

if command -v pdflatex >/dev/null; then good "pdflatex"
else bad "pdflatex ausente"; hint "rode você mesmo: ! sudo apt install -y $APT_PKGS"; fi

if [ -d private ]; then good "private/"
else bad "private/ ausente"; hint "rode: make setup"; fi

# Placeholders do modelo nos arquivos de configuração
for f in private/perfil/vagas_excluidas.md busca.yaml; do
  if [ ! -f "$f" ]; then
    case "$f" in busca.yaml) echo "aviso - $f ainda não existe (ticket 05)";; *) bad "$f ausente"; hint "rode: make setup";; esac
  elif grep -Eq 'Empresa [A-Z]\b|Recrutadora [A-Z]\b|AAAA-MM-DD' "$f"; then
    bad "placeholders em $f"; hint "preencha com seus dados reais"
  else good "$f sem placeholders"; fi
done

# Compilação do exemplo do upstream (só se tudo existir)
if command -v pdflatex >/dev/null && [ -f "$EXAMPLE_DIR/curriculo.tex" ]; then
  T="$(mktemp -d)"
  if (cd "$EXAMPLE_DIR" && pdflatex -interaction=nonstopmode -halt-on-error -output-directory "$T" curriculo.tex >"$T/log.txt" 2>&1); then
    good "exemplo do upstream compila em PDF"
  else
    bad "exemplo do upstream não compilou"; hint "veja o log: $(grep -m1 '^!' "$T/log.txt")"
    hint "provável pacote ausente: ! sudo apt install -y $APT_PKGS"
  fi
  rm -rf "$T"
fi

# Navegador do /busca (Chromium do WSL + MCP chrome-devtools). Só avisos: não afetam os currículos.
warn() { echo "aviso - $1"; }
CHROMIUM="${JOBHUNT_CHROMIUM:-/snap/bin/chromium}"
PORTA="${JOBHUNT_CDP_PORTA:-9222}"
if [ -x "$CHROMIUM" ]; then good "Chromium para o /busca ($CHROMIUM)"
else warn "Chromium não encontrado em $CHROMIUM (o /busca precisa dele)"; hint "! sudo snap install chromium (ou defina JOBHUNT_CHROMIUM)"; fi
if [ -f .mcp.json ] && grep -q '"chrome-devtools"' .mcp.json; then good ".mcp.json com chrome-devtools (aprove o MCP na 1ª vez, em /mcp)"
else warn ".mcp.json sem o servidor chrome-devtools (o /busca não alcança o navegador)"; hint "restaure o .mcp.json do repositório"; fi
if curl -fs -m 2 "http://127.0.0.1:$PORTA/json/version" >/dev/null 2>&1; then good "navegador de pé em 127.0.0.1:$PORTA"
else warn "navegador fechado (127.0.0.1:$PORTA sem resposta)"; hint "rode: make navegador"; fi

[ $BAD -eq 0 ] && echo "Ambiente pronto." || echo "Ambiente NÃO está pronto."
exit $BAD
