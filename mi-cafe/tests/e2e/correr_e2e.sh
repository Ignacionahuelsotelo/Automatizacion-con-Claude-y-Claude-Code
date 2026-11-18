#!/bin/sh
# Corre las pruebas e2e de la página (spec 26). Opcional y solo para desarrollo: ver README.md.
# Usa .venv-dev/ (Playwright), un puerto distinto de 8000/8001, datos temporales y fuentes simuladas.
set -eu
RAIZ="$(cd "$(dirname "$0")/../.." && pwd)"
PUERTO="${MICAFE_E2E_PUERTO:-8765}"
PY="$RAIZ/.venv-dev/bin/python"
[ -x "$PY" ] || { echo "Falta .venv-dev/: seguí 'Pruebas de la página' en README.md." >&2; exit 2; }
TEMPORAL="$(mktemp -d)"
trap 'rm -rf "$TEMPORAL"' EXIT
export MICAFE_DATOS="$TEMPORAL" MICAFE_E2E_URL="http://127.0.0.1:$PUERTO"
"$PY" "$RAIZ/.claude/skills/webapp-testing/scripts/with_server.py" \
  --server "\"$PY\" \"$RAIZ/tests/e2e/servidor_e2e.py\" $PUERTO" --port "$PUERTO" \
  -- "$PY" "$RAIZ/tests/e2e/e2e_pagina.py"
