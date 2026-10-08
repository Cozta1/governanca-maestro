---
name: agendar-retomada
description: Agenda qualquer ação futura necessária no projeto (o usuário autorizou), em especial a continuação de uma tarefa quando um modelo (Claude, Codex, Antigravity/Gemini) atinge ou está perto do limite de uso, usando rotinas do Maestri. Use quando um agente ou você mesmo mostrar erro de limite/cota (usage limit, rate limit, quota exceeded, 429, RESOURCE_EXHAUSTED, "try again in", "limit will reset at"), quando o Sentinela ou o usuário avisar que o limite está perto, e ANTES de iniciar tarefas longas ou lotes de delegação (rede de segurança).
---

# agendar-retomada: continuar o trabalho depois do limite

Um modelo que bate no limite não pode fazer a tarefa avançar. O maestro salva o ponto de parada no brain e agenda uma **rotina Maestri** que retoma o trabalho no horário em que **todos os agentes necessários** estarão disponíveis de novo.

> Limitação: o maestro não enxerga a própria cota restante (o `uso.py` só estima). Por isso existem dois gatilhos: **reativo** (o limite apareceu ou o Sentinela avisou) e **preventivo** (rede de segurança antes de tarefas longas).

## 0. Outras ações agendáveis
O usuário autorizou agendar **qualquer ação necessária**: extrações fora do horário de pico, relatórios, verificações periódicas, tarefas para recrutas etc. Use o mesmo padrão: checkpoint no status se houver contexto a preservar, `maestri routine list` antes, um nome descritivo, `--once` ou recorrência, e um comando que verifica antes de agir. Recorrências sem fim (`--every`/`--daily` sem `--count`/`--until`) só com motivo claro, registradas em `brain/orquestracao.md`.

## 1. Detectar
| Agente | Sinais típicos |
|---|---|
| Claude Code | "usage limit", "limit will reset at <hora>", "5-hour limit", "approaching usage limit" |
| Codex | "You've hit your usage limit", "try again in <tempo>", "rate limit" |
| Antigravity/Gemini | "quota exceeded", "RESOURCE_EXHAUSTED", HTTP 429 |
| Sentinela | mensagem "Sentinela de uso: ..." (75% ou desequilíbrio de 35 pontos ou mais) |

Leia a saída dos recrutas com `maestri check "<Nome>"`. Se o aviso disser o horário de reset, use esse horário. `uso.py status` mostra os resets do Codex (exatos) e do Claude (estimado).

## 2. Antes de agendar: realocar, se der
Se outro modelo **disponível** pode fazer a tarefa (ver a tabela de modelos em `brain/orquestracao.md`), delegue a ele agora em vez de esperar. Por exemplo, com o Codex no limite, a revisão vai para um subagente Claude ou para um recruta Antigravity. Só agende quando ninguém adequado estiver livre ou quando a tarefa exigir aquele modelo.

## 3. Salvar o ponto de parada (checkpoint)
Em `brain/status.md`, crie ou atualize a seção `## Retomada agendada` com:
- **Tarefa:** o que estava sendo feito, com links `[[nota]]`.
- **Feito até agora:** arquivos alterados e estado.
- **Próximo passo exato:** comando ou ação.
- **Agentes envolvidos** e o horário de reset de cada um.
- **Rotina:** nome e horário.

Arquivos de código já editados ficam no disco. Se o trabalho estiver num floor, registre o nome do floor.

## 4. Calcular o horário
- Horário de reset conhecido: use o **maior** reset entre os agentes necessários + **5 min** de margem.
- Desconhecido: use 1 h para Codex/Gemini e 5 h para Claude (janela de uso), e registre como estimativa.
- Formato: `yyyy-MM-dd HH:mm` no horário local (veja com `date "+%Y-%m-%d %H:%M"`).

## 5. Agendar a rotina
```bash
M=$(command -v maestri || echo "$MAESTRI_CLI")
"$M" routine list   # sempre antes, para não duplicar
# Maestro retomando a si mesmo (alvo padrão = o próprio terminal):
"$M" routine create "Retomar: <tarefa curta>" --once "<AAAA-MM-DD HH:mm>" \
  --command "Retomada agendada: leia a seção 'Retomada agendada' de brain/status.md e continue a tarefa a partir do próximo passo. Verifique antes se ainda está pendente; se já estiver concluída, só limpe a seção."
# Recruta retomando (ex.: Codex):
"$M" routine create "Retomar: <tarefa> (<Nome>)" --once "<AAAA-MM-DD HH:mm>" --terminal "<Nome>" \
  --command "<a mesma tarefa que tinha sido pedida, autocontida>"
```
- Uma rotina **por agente** que precisa retomar. Se o maestro precisa integrar o resultado, agende a rotina dele **depois** da do recruta, com uma margem a mais.
- Por padrão a rotina é pulada se o terminal estiver ocupado. Use `--no-skip-if-busy` só se tiver certeza de que não vai atropelar trabalho em curso.
- Avise o usuário: o que foi agendado, quando e por quê.

## 6. Rede de segurança preventiva
Antes de uma tarefa longa (vários passos, lote de `maestri ask --batch`, scaffold grande):
1. Escreva o checkpoint (passo 3) com o plano da tarefa.
2. Crie a rotina `"Rede: <tarefa>"` com `--once` em agora + 5 h 10 min, e um comando que **verifica antes de agir** (como o do passo 5).
3. Ao concluir a tarefa normalmente: `maestri routine disable "Rede: <tarefa>"` e limpe a seção do status. Não apague a rotina: `delete` só com pedido explícito do usuário.

## 7. Ao retomar
- Leia o checkpoint (use `brain-search`), confira o estado real (arquivos, `maestri check`) e continue.
- Ao terminar: remova a seção `## Retomada agendada` do status, registre no `brain/diario.md` e desative rotinas de rede pendentes.
