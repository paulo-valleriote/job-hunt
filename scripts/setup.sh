#!/usr/bin/env bash
# Prepara o ambiente: upstream, venv, private/ e cópia única dos dados do usuário.
# Variáveis de ambiente (padrões do spec):
#   JOBHUNT_SOURCE_DIR   origem dos dados (/mnt/e/busca-vagas/privado)
#   JOBHUNT_UPSTREAM_URL URL do upstream
#   JOBHUNT_SKIP_PIP=1   não instala dependências (testes)
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT" || exit 1
SOURCE="${JOBHUNT_SOURCE_DIR:-/mnt/e/busca-vagas/privado}"
UPSTREAM="${JOBHUNT_UPSTREAM_URL:-https://github.com/R238Company/meu-emprego-novo.git}"
VENDOR=vendor/meu-emprego-novo
DONE=(); SKIPPED=(); WARN=0

# 1. Upstream (somente clone; nunca modificado)
if [ -d "$VENDOR/.git" ]; then
  SKIPPED+=("upstream já clonado em $VENDOR")
else
  mkdir -p vendor
  if git clone --quiet "$UPSTREAM" "$VENDOR"; then DONE+=("upstream clonado em $VENDOR")
  else echo "ERRO: falha ao clonar $UPSTREAM" >&2; exit 1; fi
fi

# 2. venv
if [ -x venv/bin/python ]; then SKIPPED+=("venv já existe")
else
  python3 -m venv venv || { echo "ERRO: falha ao criar venv" >&2; exit 1; }
  DONE+=("venv criado")
fi
if [ "${JOBHUNT_SKIP_PIP:-0}" = 1 ]; then SKIPPED+=("instalação de dependências (JOBHUNT_SKIP_PIP=1)")
else
  venv/bin/pip install --quiet -r requirements.txt && DONE+=("dependências instaladas") \
    || { echo "ERRO: falha no pip install" >&2; exit 1; }
fi

# 3. Estrutura de private/
mkdir -p private/perfil private/vagas private/curriculos
DONE+=("estrutura private/ garantida")

# 4. Cópia única dos dados (nunca sobrescreve; origem só é lida)
copy_once() { # origem relativa -> destino relativo a private/
  local src="$SOURCE/$1" dst="private/$2"
  if [ -e "$dst" ]; then SKIPPED+=("pulado (já existe): $dst")
  elif [ -f "$src" ]; then cp -n "$src" "$dst" && DONE+=("copiado: $2")
  else SKIPPED+=("pulado (origem ausente): $src"); WARN=1; fi
}
copy_once perfil/profile_truth.md    perfil/profile_truth.md
copy_once perfil/resume.pdf          perfil/resume.pdf
copy_once perfil/vagas_excluidas.md  perfil/vagas_excluidas.md
copy_once perfil/tracker.csv         tracker.csv

# 5. Checagem de privacidade do upstream
echo "== checar_privacidade.sh =="
CHK="$VENDOR/meu-emprego-novo-pipeline/scripts/checar_privacidade.sh"
if [ -f "$CHK" ]; then bash "$CHK" || echo "(checar_privacidade.sh saiu com código $?)"
else echo "script não encontrado: $CHK"; WARN=1; fi

echo "== Resumo =="
for m in "${DONE[@]}"; do echo "feito:  $m"; done
for m in "${SKIPPED[@]}"; do echo "pulado: $m"; done
exit 0
