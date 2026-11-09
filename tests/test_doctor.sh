#!/usr/bin/env bash
# Testes do scripts/doctor.sh via `make doctor`, com binários falsos no PATH.
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FAILS=0
ok()   { echo "ok   - $1"; }
fail() { echo "FAIL - $1"; FAILS=$((FAILS+1)); }
check() { local d="$1"; shift; if "$@" >/dev/null 2>&1; then ok "$d"; else fail "$d"; fi; }
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT

PROJ="$TMP/proj"; mkdir -p "$PROJ"
(cd "$ROOT" && git ls-files -co --exclude-standard | grep -v "^\.scratch" | rsync -a --files-from=- . "$PROJ/")
FAKE="$TMP/bin"; mkdir -p "$FAKE"
mkfake() { printf '#!/bin/sh\necho fake\n' > "$FAKE/$1"; chmod +x "$FAKE/$1"; }
# PATH isolado: espelha /usr/bin sem pdflatex/claude reais (o ambiente pode ter LaTeX instalado)
REAL="$TMP/realbin"; mkdir -p "$REAL"
for f in /usr/bin/* /bin/*; do b="${f##*/}"; case "$b" in pdflatex|claude) ;; *) ln -sf "$f" "$REAL/$b" 2>/dev/null;; esac; done
doctor() { (cd "$PROJ" && PATH="$FAKE:$REAL" make doctor 2>&1); }

# Cenário 1: nada pronto (sem claude, pdflatex, private/)
OUT="$(doctor)"; RC=$?
check "falha quando falta ambiente" test $RC -ne 0
check "aponta pdflatex ausente" grep -q "pdflatex" <<<"$OUT"
check "aponta claude ausente" grep -qi "claude" <<<"$OUT"
check "aponta private/ ausente e sugere make setup" grep -q "make setup" <<<"$OUT"
check "devolve comando exato com sudo apt" grep -q '! sudo apt install .*texlive' <<<"$OUT"
check "doctor não executa sudo" bash -c "! grep -E '^[[:space:]]*sudo ' $ROOT/scripts/doctor.sh"

# Cenário 2: binários presentes, private/ com placeholders
mkfake claude; mkfake pdflatex
mkdir -p "$PROJ/private/perfil"
echo "Empresa A | AAAA-MM-DD" > "$PROJ/private/perfil/vagas_excluidas.md"
OUT="$(doctor)"; RC=$?
check "falha com placeholders" test $RC -ne 0
check "aponta placeholders em vagas_excluidas.md" grep -q "placeholder.*vagas_excluidas\|vagas_excluidas.*placeholder" <<<"$OUT"
check "não pede mais sudo apt" bash -c "! grep -q 'sudo apt' <<<'$OUT'"

# Cenário 3: tudo pronto
echo "Empresa Real | 2025-01-10" > "$PROJ/private/perfil/vagas_excluidas.md"
OUT="$(doctor)"; RC=$?
check "sucesso com ambiente pronto" test $RC -eq 0

# Cenário 4: navegador do /busca (avisos; não derrubam o "Ambiente pronto" dos currículos)
PORTA=$(python3 -c 'import socket;s=socket.socket();s.bind(("127.0.0.1",0));print(s.getsockname()[1])')
export JOBHUNT_CDP_PORTA=$PORTA JOBHUNT_CHROMIUM="$TMP/nao-existe/chromium"
OUT="$(doctor)"; RC=$?
check "navegador ausente não derruba o ambiente" test $RC -eq 0
check "avisa Chromium ausente" grep -qi "aviso.*chromium" <<<"$OUT"
check "avisa porta fechada e sugere make navegador" grep -q "make navegador" <<<"$OUT"
check "reconhece .mcp.json com chrome-devtools" grep -q "ok .*\.mcp\.json" <<<"$OUT"
rm -f "$PROJ/.mcp.json"
OUT="$(doctor)"; RC=$?
check "avisa .mcp.json ausente" grep -qi "aviso.*\.mcp\.json" <<<"$OUT"
mkdir -p "$TMP/srv/json"; echo '{}' > "$TMP/srv/json/version"; printf '#!/bin/sh\n' > "$FAKE/chromium-ok"; chmod +x "$FAKE/chromium-ok"
(cd "$TMP/srv" && python3 -m http.server "$PORTA" --bind 127.0.0.1 >/dev/null 2>&1) & SRV=$!
for _ in 1 2 3 4 5 6 7 8 9 10; do curl -fs -m 1 "http://127.0.0.1:$PORTA/json/version" >/dev/null 2>&1 && break; sleep 0.3; done
JOBHUNT_CHROMIUM="$FAKE/chromium-ok" OUT="$(doctor)"
kill $SRV 2>/dev/null
check "navegador de pé: ok na porta e sem aviso de Chromium" bash -c "grep -q 'ok .*127.0.0.1' <<<'$OUT' && ! grep -qi 'aviso.*chromium' <<<'$OUT'"
unset JOBHUNT_CDP_PORTA JOBHUNT_CHROMIUM

[ $FAILS -eq 0 ] && echo "TODOS OK" || { echo "$FAILS falha(s)"; exit 1; }
