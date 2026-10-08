#!/bin/sh
# Instala (ou atualiza) a skill governanca-maestro e o atalho no CLAUDE.md global.
# Uso: sh instalar.sh   (no Windows, pelo Git Bash)
set -e
AQUI=$(cd "$(dirname "$0")" && pwd)
DESTINO="$HOME/.claude/skills/governanca-maestro"
GLOBAL="$HOME/.claude/CLAUDE.md"

mkdir -p "$HOME/.claude/skills"
rm -rf "$DESTINO"
cp -r "$AQUI/governanca-maestro" "$DESTINO"
echo "skill instalada em $DESTINO"

if ! grep -q "governanca-maestro" "$GLOBAL" 2>/dev/null; then
  cat >> "$GLOBAL" <<'EOF'

## Governança de projetos (skill governanca-maestro)
Quando eu pedir para "seguir o repo" para definir a estrutura base e a governança de um projeto (ou "aplicar a governança", "bootstrap"), use a skill `governanca-maestro`: monte a estrutura (seção 11) e, logo em seguida, conduza o planejamento comigo (seção 12). O primeiro passo de todo projeto é definir o plano.
Se a skill não estiver instalada: `git clone https://github.com/Cozta1/governanca-maestro.git` numa pasta temporária e rode `sh instalar.sh` de lá.
EOF
  echo "atalho adicionado em $GLOBAL"
else
  echo "atalho já existe em $GLOBAL"
fi
