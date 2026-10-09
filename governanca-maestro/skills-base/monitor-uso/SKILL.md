---
name: monitor-uso
description: Consulta os limites de uso do Claude, do Codex e do Gemini via Antigravity (exatos: janela de 5 h e semana) para decidir para qual família de modelo delegar e evitar paradas forçadas. Use antes de distribuir tarefas, quando o Sentinela avisar, ou quando o usuário perguntar sobre limites e equilíbrio de uso.
---

# monitor-uso: limites de uso e equilíbrio Claude × Codex

Script: `python .claude/skills/monitor-uso/uso.py <status|json|vigiar>`

| Família | Fonte | Precisão |
|---|---|---|
| Codex | `rate_limits` nos rollouts de `~/.codex/sessions` (janela de 5 h e semanal, com horário de reset) | exata |
| Claude | API de uso da Anthropic (`/api/oauth/usage`, a mesma do `/usage`) com o login OAuth local; o token só vai para api.anthropic.com. Reserva, se a API falhar: tokens ponderados em `~/.claude/projects/*/*.jsonl` calibrados pela última rejeição 429 | exata (janela de 5 h e semana) |

As duas medições valem para a **conta inteira** (todos os projetos), não só para este.
A saída recomenda `preferir: codex|claude|equilibrado`, conforme qual família tem mais folga (diferença maior que 10 pontos).

## Sentinela (agente Shell no canvas, sem custo de modelo)
- Roda `uso.py vigiar --intervalo 120 --limite 75`. O terminal avisado é o escrito em `sentinela-alvo.txt`, ao lado do script: o nome do terminal do maestro, como aparece em `maestri list`.
- Avisa o maestro via `maestri ask` quando:
  - alguma janela passa de 75%;
  - o semanal do Codex passa de 75%;
  - o uso fica desequilibrado (diferença de 35 pontos ou mais).
- Cada alerta é enviado uma vez e é rearmado quando a situação normaliza.
- Criar (Modo Maestro, uma vez por projeto; antes rode `maestri list` e não duplique):
  ```bash
  M=$(command -v maestri || echo "$MAESTRI_CLI")
  "$M" recruit "Sentinela" --preset "Shell" --command "python <projeto>/.claude/skills/monitor-uso/uso.py vigiar --intervalo 120 --limite 75"
  ```
  Use o caminho absoluto do projeto, com `/` e sem aspas internas (o terminal é PowerShell). Confira com `maestri check "Sentinela"`: a primeira linha diz quem ele avisa.

## Ao receber um alerta
1. Rode `uso.py status`.
2. **Família perto do limite:**
   - não inicie tarefas longas nela; passe o próximo trabalho para a outra família, que é de primeira linha nos dois casos (`brain/orquestracao.md`);
   - se a tarefa em andamento não puder mudar de família, aplique a skill `agendar-retomada` (checkpoint + rotina no reset).
3. **Se o próprio maestro (Claude) estiver acima de 85%:**
   - grave o checkpoint em `brain/status.md`;
   - delegue o restante ao Codex com instruções completas;
   - agende a retomada.
4. **Desequilíbrio:** nas próximas delegações, priorize a família com mais folga, inclusive nos campos em que ela é "alternativa" na tabela de modelos.
