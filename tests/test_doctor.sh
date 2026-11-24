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

# API falsa do Rebase (local, sem rede): token tok-401 -> 401, tok-403 -> 403, demais -> 200.
# Sobe já aqui, para que nenhum cenário do doctor alcance rebasedev.com.br.
LOG="$TMP/api.log"; : > "$LOG"
cat > "$TMP/fake_api.py" <<'PY'
import http.server, sys
LOG = sys.argv[2]
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        auth = self.headers.get("Authorization", "")
        with open(LOG, "a") as f:
            f.write(self.path + "\n")
        code = 401 if "tok-401" in auth else 403 if "tok-403" in auth else 200
        body = b'{"data":[],"meta":{"total":0,"pagina":1,"paginas":1,"por_pagina":1}}' if code == 200 \
            else b'{"error":{"code":"x","message":"y"}}'
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)
    def log_message(self, *a):
        pass
http.server.HTTPServer(("127.0.0.1", int(sys.argv[1])), H).serve_forever()
PY
APIPORTA=$(python3 -c 'import socket;s=socket.socket();s.bind(("127.0.0.1",0));print(s.getsockname()[1])')
python3 "$TMP/fake_api.py" "$APIPORTA" "$LOG" >/dev/null 2>&1 & API=$!
for _ in 1 2 3 4 5 6 7 8 9 10; do curl -s -m 1 -o /dev/null "http://127.0.0.1:$APIPORTA/api/v1/jobs" && break; sleep 0.3; done
export JOBHUNT_REBASE_API="http://127.0.0.1:$APIPORTA/api/v1"

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
echo "TOKEN=tok-200" > "$PROJ/private/rebase.env"
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

# Cenário 5: Rebase (API falsa do topo). Só conta chamadas.
rm -f "$PROJ/private/rebase.env"; : > "$LOG"
OUT="$(doctor)"; RC=$?
check "sem rebase.env: falha com instrução de TOKEN" bash -c "grep -q 'grave TOKEN= em private/rebase.env' <<<'$OUT' && test $RC -ne 0"
check "sem token não chama a API" test "$(wc -l < "$LOG")" -eq 0

echo "TOKEN=tok-401" > "$PROJ/private/rebase.env"; : > "$LOG"
OUT="$(doctor)"; RC=$?
check "401 vira 'token recusado (401)'" bash -c "grep -q 'token recusado (401)' <<<'$OUT' && test $RC -ne 0"
check "401: uma única chamada" test "$(wc -l < "$LOG")" -eq 1

echo "TOKEN=tok-403" > "$PROJ/private/rebase.env"; : > "$LOG"
OUT="$(doctor)"; RC=$?
check "403 vira 'sem aceite (403)'" bash -c "grep -q 'sem aceite (403)' <<<'$OUT' && test $RC -ne 0"

echo "TOKEN=tok-200" > "$PROJ/private/rebase.env"; : > "$LOG"
OUT="$(doctor)"; RC=$?
check "200 vira ok" bash -c "grep -q 'ok .*Rebase' <<<'$OUT' && test $RC -eq 0"
check "200: uma única chamada a /jobs?por_pagina=1" bash -c "test \"\$(wc -l < '$LOG')\" -eq 1 && grep -q 'jobs?por_pagina=1' '$LOG'"
check "token nunca aparece na saída do doctor" bash -c "! grep -q 'tok-200' <<<'$OUT'"
# Cenário 6: base da API fora de rebasedev.com.br e loopback é recusada, sem chamada e sem token na saída
echo "TOKEN=tok-200" > "$PROJ/private/rebase.env"; : > "$LOG"
OUT="$(JOBHUNT_REBASE_API="https://evil.example.com/api/v1" doctor)"; RC=$?
check "base estranha: falha com 'base da API não permitida'" bash -c "grep -q 'base da API não permitida' <<<'$OUT' && test $RC -ne 0"
check "base estranha: token nunca aparece na saída" bash -c "! grep -q 'tok-200' <<<'$OUT'"
check "base estranha: nenhuma chamada à API local" test "$(wc -l < "$LOG")" -eq 0

kill $API 2>/dev/null
unset JOBHUNT_REBASE_API

[ $FAILS -eq 0 ] && echo "TODOS OK" || { echo "$FAILS falha(s)"; exit 1; }
