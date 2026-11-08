#!/usr/bin/env bash
# Testes do scripts/setup.sh. Usam fixtures falsas em diretório temporário;
# nunca tocam em /mnt/e nem em dados reais.
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FAILS=0
ok()   { echo "ok   - $1"; }
fail() { echo "FAIL - $1"; FAILS=$((FAILS+1)); }
check() { local d="$1"; shift; if "$@" >/dev/null 2>&1; then ok "$d"; else fail "$d"; fi; }

TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT

# Upstream falso (repositório git local)
UP="$TMP/upstream"; mkdir -p "$UP/meu-emprego-novo-pipeline/scripts"
cat > "$UP/meu-emprego-novo-pipeline/scripts/checar_privacidade.sh" <<'S'
#!/usr/bin/env bash
echo "PRIVACIDADE-FAKE-OK"
S
git -C "$UP" init -q && git -C "$UP" add . \
  && git -C "$UP" -c user.name=t -c user.email=t@t commit -qm init

# Origem falsa dos dados do usuário
SRC="$TMP/src"; mkdir -p "$SRC/perfil"
for f in profile_truth.md resume.pdf tracker.csv vagas_excluidas.md; do
  echo "fake-$f" > "$SRC/perfil/$f"
done
cp -r "$SRC" "$TMP/src.orig"

# Projeto sob teste: cópia dos arquivos rastreados
PROJ="$TMP/proj"; mkdir -p "$PROJ"
(cd "$ROOT" && git ls-files -co --exclude-standard | grep -v "^\.scratch" | rsync -a --files-from=- . "$PROJ/")

run() {
  (cd "$PROJ" && JOBHUNT_SOURCE_DIR="$SRC" JOBHUNT_UPSTREAM_URL="$UP" \
     JOBHUNT_SKIP_PIP=1 make setup 2>&1)
}

OUT1="$(run)"; RC=$?
check "make setup termina com sucesso" test $RC -eq 0
check "clona upstream em vendor/meu-emprego-novo" test -f "$PROJ/vendor/meu-emprego-novo/meu-emprego-novo-pipeline/scripts/checar_privacidade.sh"
check "cria venv" test -x "$PROJ/venv/bin/python"
check "cria estrutura private/" bash -c "cd $PROJ/private && test -d perfil && test -d vagas && test -d curriculos"
check "copia profile_truth.md" cmp "$SRC/perfil/profile_truth.md" "$PROJ/private/perfil/profile_truth.md"
check "copia resume.pdf" cmp "$SRC/perfil/resume.pdf" "$PROJ/private/perfil/resume.pdf"
check "copia vagas_excluidas.md" cmp "$SRC/perfil/vagas_excluidas.md" "$PROJ/private/perfil/vagas_excluidas.md"
check "copia tracker.csv para private/tracker.csv" cmp "$SRC/perfil/tracker.csv" "$PROJ/private/tracker.csv"
check "originais intactos" diff -r "$SRC" "$TMP/src.orig"
check "mostra resultado do checar_privacidade" grep -q "PRIVACIDADE-FAKE-OK" <<<"$OUT1"
check "informa o que copiou" grep -qi "copiado" <<<"$OUT1"

# Reexecução: não sobrescreve
echo "EDITADO" > "$PROJ/private/perfil/profile_truth.md"
OUT2="$(run)"; RC=$?
check "reexecução termina com sucesso" test $RC -eq 0
check "não sobrescreve dado existente" grep -q EDITADO "$PROJ/private/perfil/profile_truth.md"
check "informa o que pulou" grep -qi "pulado" <<<"$OUT2"

# Upstream não é modificado nem rastreado
check "vendor e private ignorados pelo git" bash -c "cd $ROOT && git check-ignore -q vendor/x && git check-ignore -q private/x"

[ $FAILS -eq 0 ] && echo "TODOS OK" || { echo "$FAILS falha(s)"; exit 1; }
