#!/bin/sh
# Instala (ou atualiza) a skill governanca-maestro, o atalho no CLAUDE.md global
# e os papéis de subagente do Codex (explorador e revisor) em ~/.codex.
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

# Papéis de subagente do Codex: Sol constrói, Luna explora, Sol xhigh revisa (nunca gpt-6-astra).
CODEX="$HOME/.codex"
if [ -d "$CODEX" ]; then
  mkdir -p "$CODEX/agents"
  cp "$AQUI/codex/agents/explorador.toml" "$AQUI/codex/agents/revisor.toml" "$CODEX/agents/"
  CFG="$CODEX/config.toml"
  if ! grep -q '^\[agents\.explorador\]' "$CFG" 2>/dev/null; then
    [ -f "$CFG" ] && cp "$CFG" "$CFG.bak-governanca"
    BASE=$(cd "$CODEX/agents" && (pwd -W 2>/dev/null || pwd))
    {
      echo ""
      echo "# --- governanca-maestro: papéis de subagente (instalar.sh) ---"
      echo "[agents.explorador]"
      echo 'description = "Explora arquivos, codigo e documentacao em paralelo; so leitura; devolve arquivo:linha e resumo curto."'
      echo "config_file = \"$BASE/explorador.toml\""
      echo ""
      echo "[agents.revisor]"
      echo 'description = "Assessor: revisa planos, desbloqueia erros repetidos e faz a conferencia final antes de concluir; so leitura."'
      echo "config_file = \"$BASE/revisor.toml\""
    } >> "$CFG"
    echo "papéis explorador/revisor adicionados em $CFG (backup: $CFG.bak-governanca)"
  else
    echo "papéis do Codex já existem em $CFG (arquivos .toml atualizados)"
  fi
else
  echo "Codex não encontrado (~/.codex); papéis de subagente ignorados"
fi
