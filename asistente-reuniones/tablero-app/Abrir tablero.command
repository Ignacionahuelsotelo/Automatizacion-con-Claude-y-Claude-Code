#!/bin/bash
# Doble clic para abrir el tablero. Se queda corriendo en esta ventana: cerrala para apagarlo.
cd "$(dirname "$0")" || exit 1

# Terminal no carga la configuración de tu usuario: sumamos a mano dónde viven node y claude.
NODO="$(ls -d "$HOME"/.nvm/versions/node/*/bin 2>/dev/null | sort -V | tail -1)"
export PATH="${NODO:+$NODO:}$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"

faltan=""
command -v npm    >/dev/null || faltan="$faltan npm (Node.js)"
command -v claude >/dev/null || faltan="$faltan claude"
if [ -n "$faltan" ]; then
  echo "No encuentro:$faltan"
  echo "Instalalo o avisale a Claude. Esta ventana se puede cerrar."
  read -r -p "Enter para salir"
  exit 1
fi

[ -d node_modules ] || npm install || exit 1
npm run build || { read -r -p "Falló la compilación. Enter para salir"; exit 1; }
(sleep 3; open "http://127.0.0.1:3210") &
exec npm start
