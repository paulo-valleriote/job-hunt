#!/usr/bin/env bash
# Abre o Chromium (WSLg) com a porta de debug em 127.0.0.1:9222 e um perfil dedicado,
# usado pelo MCP chrome-devtools (.mcp.json) no /busca. O perfil fica FORA do repositório
# e só deve ter o login do LinkedIn (a porta de debug dá controle total deste navegador).
set -euo pipefail

PORTA="${JOBHUNT_CDP_PORTA:-9222}"
PERFIL="${JOBHUNT_PERFIL_NAVEGADOR:-$HOME/chromium-linkedin-profile}"
BIN="${JOBHUNT_CHROMIUM:-/snap/bin/chromium}"

if curl -fs -m 2 "http://127.0.0.1:${PORTA}/json/version" >/dev/null 2>&1; then
  echo "Navegador já está de pé em 127.0.0.1:${PORTA}."
  exit 0
fi

[ -x "$BIN" ] || { echo "Chromium não encontrado em $BIN (defina JOBHUNT_CHROMIUM)." >&2; exit 1; }
[ -n "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ] || { echo "Sem DISPLAY: WSLg não está ativo." >&2; exit 1; }

mkdir -p "$PERFIL"
nohup "$BIN" \
  --remote-debugging-port="$PORTA" --remote-debugging-address=127.0.0.1 \
  --user-data-dir="$PERFIL" --no-first-run --no-default-browser-check about:blank \
  >/dev/null 2>&1 &

for _ in $(seq 1 20); do
  if curl -fs -m 2 "http://127.0.0.1:${PORTA}/json/version" >/dev/null 2>&1; then
    echo "Navegador pronto em 127.0.0.1:${PORTA} (perfil: $PERFIL)."
    echo "Se for a primeira vez, entre você mesmo no LinkedIn nessa janela."
    exit 0
  fi
  sleep 1
done
echo "O navegador não respondeu na porta ${PORTA}." >&2
exit 1
