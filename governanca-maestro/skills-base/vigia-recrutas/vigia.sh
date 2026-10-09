#!/usr/bin/env bash
# vigia.sh: aprova UMA vez, e só se for seguro, os pedidos de confirmação de comandos dos recrutas
# Codex ("Press enter to confirm") e Antigravity/agy ("Requesting permission for:").
# Para no primeiro pedido que não for claramente seguro e deixa uma linha PARAR em vigia.log.
#
# Uso (Git Bash, em segundo plano, a partir do scratchpad do maestro):
#   bash vigia.sh [-i SEGUNDOS] Nome:codex Nome2:agy ...      # padrão: 5 s
#   MAESTRI_CLI=/caminho/maestri bash vigia.sh Backend:codex Front:agy &
# Nunca escolhe "não perguntar de novo". Não faz push, exclusão, download nem instalação global.
set -u
INTERVALO=5
if [ "${1:-}" = "-i" ]; then INTERVALO="$2"; shift 2; fi
[ $# -gt 0 ] || { echo "uso: vigia.sh [-i s] Nome:codex|agy ..." >&2; exit 2; }
M="${MAESTRI_CLI:-$(command -v maestri || true)}"
[ -n "$M" ] || { echo "maestri não encontrado (defina MAESTRI_CLI)" >&2; exit 2; }
LOG="${VIGIA_LOG:-vigia.log}"
log() { printf '%s %s\n' "$(date '+%H:%M:%S')" "$*" | tee -a "$LOG"; }

# Cada trecho do comando (separado por && || ; |) precisa casar com a lista segura.
SEGURO='^(cd [^ ]+|ls( .*)?|pwd|cat [^ ]+|head .*|tail .*|grep .*|rg .*|find [^ ]+ .*|wc .*|sed -n .*|'\
'git (status|diff|log|show|branch|add .*|commit .*|rev-parse .*|ls-files.*)|'\
'(pnpm|npm|yarn) (install|i|ci|test|run (test|typecheck|lint|build)[^ ]*|typecheck|lint|build|exec (vitest|tsc|eslint).*)( .*)?|'\
'pnpm (-r |--filter [^ ]+ )?(test|typecheck|lint|build|install)( .*)?|'\
'(npx )?(vitest|tsc|eslint|prettier --check)( .*)?|'\
'docker compose (ps|logs)( .*)?)$'
# Qualquer um destes bloqueia, mesmo dentro de um comando que pareceria seguro.
PERIGO='(rm |rmdir|del |Remove-Item|-delete|-exec|\.env|git push|git reset|git clean|git checkout --|git rebase|--force|-f |curl|wget|Invoke-WebRequest|iwr |npm (i|install) (-g|--global)|pnpm (add|install) (-g|--global)|docker compose (down|rm|up)|docker (rm|volume|system)|-v( |$)|drop |DROP |migrate reset|sudo|chmod|>|`|\$\()'

seguro() { # $1 = comando completo
  local cmd="$1" parte
  [ -n "$cmd" ] || return 1
  printf '%s' "$cmd" | grep -Eq "$PERIGO" && return 1
  cmd=${cmd//&&/$'\n'}; cmd=${cmd//||/$'\n'}; cmd=${cmd//;/$'\n'}; cmd=${cmd//|/$'\n'}
  while IFS= read -r parte; do
    parte=$(printf '%s' "$parte" | sed -E 's/^[[:space:]]+|[[:space:]]+$//g')
    [ -z "$parte" ] && continue
    printf '%s' "$parte" | grep -Eq "$SEGURO" || return 1
  done <<< "$cmd"
  return 0
}

extrair() { # $1 = formato, $2 = tela; imprime o comando pedido (vazio se não achar)
  case "$1" in
    agy)   printf '%s\n' "$2" | awk '/Requesting permission for:/{f=1;next} f&&NF{print;exit}' ;;
    codex) printf '%s\n' "$2" | awk '/run the following command|Command:/{f=1;next} f&&NF{print;exit}' ;;
  esac | sed -E 's/^[[:space:]]*(\$|>|[0-9]+\.)?[[:space:]]*//; s/[[:space:]]+$//'
}

pendente() { # $1 = formato, $2 = tela
  case "$1" in
    agy)   printf '%s\n' "$2" | grep -q 'Requesting permission for:' ;;
    codex) printf '%s\n' "$2" | grep -q 'Press enter to confirm' ;;
  esac
}

aprovar() { # $1 = nome, $2 = formato
  case "$2" in
    agy)   "$M" ask "$1" --raw $'\r' >/dev/null 2>&1 ;;  # opção 1 = Enter
    codex) "$M" ask "$1" --raw "y" >/dev/null 2>&1 ;;
  esac
}

declare -A ULTIMO   # assinatura do último pedido aprovado por recruta
log "vigia iniciada: $* (a cada ${INTERVALO}s)"
while true; do
  for alvo in "$@"; do
    nome="${alvo%%:*}"; fmt="${alvo##*:}"
    case "$fmt" in codex|agy) ;; *) log "PARAR: formato inválido em '$alvo' (use :codex ou :agy)"; exit 2 ;; esac
    tela=$("$M" check "$nome" 2>/dev/null | tail -n 40)
    pendente "$fmt" "$tela" || { ULTIMO[$nome]=""; continue; }
    cmd=$(extrair "$fmt" "$tela")
    assinatura=$(printf '%s' "$cmd" | cksum)
    if [ "${ULTIMO[$nome]:-}" = "$assinatura" ]; then
      log "PARAR: $nome continua pedindo o mesmo comando depois da aprovação: $cmd"; exit 1
    fi
    if seguro "$cmd"; then
      aprovar "$nome" "$fmt"
      ULTIMO[$nome]="$assinatura"
      log "aprovado ($nome): $cmd"
    else
      log "PARAR: $nome pede um comando que não é claramente seguro: ${cmd:-<não consegui ler o comando>}"
      exit 1
    fi
  done
  sleep "$INTERVALO"
done
