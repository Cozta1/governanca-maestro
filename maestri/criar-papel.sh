#!/bin/sh
# Cria (ou atualiza) o papel global "Maestro Governanca" no Maestri a partir de maestro-governanca.md.
# Rode num terminal do Maestri em Modo Maestro: sh maestri/criar-papel.sh
set -e
AQUI=$(cd "$(dirname "$0")" && pwd)
M=$(command -v maestri || echo "$MAESTRI_CLI")
[ -n "$M" ] || { echo "maestri CLI não encontrado (rode dentro do Maestri)"; exit 1; }
NOME="Maestro Governanca"
PROMPT=$(cat "$AQUI/maestro-governanca.md")
if "$M" role list 2>/dev/null | grep -q "\"$NOME\""; then
  "$M" role write "$NOME" "$PROMPT"
  "$M" role edit "$NOME" --scope global >/dev/null 2>&1 || true
  echo "papel \"$NOME\" atualizado"
else
  "$M" role create "$NOME" "$PROMPT" --scope global
  echo "papel \"$NOME\" criado (global)"
fi
