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
doctor() { (cd "$PROJ" && PATH="$FAKE:/usr/bin:/bin" make doctor 2>&1); }

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

[ $FAILS -eq 0 ] && echo "TODOS OK" || { echo "$FAILS falha(s)"; exit 1; }
