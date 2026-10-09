---
name: monitor-uso
description: Consulta os limites de uso do Claude, do Codex e do Gemini via Antigravity (exatos: janela de 5 h e semana) para decidir para qual família de modelo delegar e evitar paradas forçadas. Use antes de distribuir tarefas, quando o Sentinela avisar, ou quando o usuário perguntar sobre limites e equilíbrio de uso.
---

# monitor-uso: limites de uso e equilíbrio Claude × Codex × Gemini

Script: `python .claude/skills/monitor-uso/uso.py <status|json|vigiar|sentinela>`

| Família | Fonte | Precisão |
|---|---|---|
| Codex | `rate_limits` nos rollouts de `~/.codex/sessions` (janela de 5 h e semanal, com horário de reset) | exata |
| Claude | API de uso da Anthropic (`/api/oauth/usage`, a mesma do `/usage`) com o login OAuth local; o token só vai para api.anthropic.com. Reserva, se a API falhar: tokens ponderados em `~/.claude/projects/*/*.jsonl` calibrados pela última rejeição 429 | exata (janela de 5 h e semana) |
| Gemini | `agy -p /usage --output-format json` (Antigravity), grupo "Gemini Models", buckets `5h` e `weekly` (`remaining_fraction`, `reset_time`); cache de 10 min. Caminho do `agy` em `AGY_CLI`, se não for o padrão `~/.gemini/bin` | exata (janela de 5 h e semana) |

As três medições valem para a **conta inteira** (todos os projetos), não só para este.
Os modelos Claude/GPT do Antigravity têm cota separada (grupo "Claude and GPT models"), que o `uso.py` não lê: serve de reserva quando a assinatura Claude estiver no limite.
A saída recomenda `preferir: claude|codex|gemini|equilibrado`, conforme qual família tem mais folga (diferença maior que 10 pontos sobre as demais).

## Sentinela (agente Shell no canvas, sem custo de modelo)
- Roda `uso.py vigiar --intervalo 120 --limite 75`. O terminal avisado é o escrito em `sentinela-alvo.txt`, ao lado do script: o nome do terminal do maestro, como aparece em `maestri list`.
- O painel do `vigiar` mostra barras coloridas por família (verde < 50%, amarelo < 75%, vermelho ≥ 75%), os horários de reinício em dd/mm e os últimos alertas.
- Avisa o maestro via `maestri ask` quando:
  - alguma janela de qualquer das três famílias passa de 75%;
  - o semanal de qualquer das três passa de 75%;
  - o uso fica desequilibrado (diferença de 35 pontos ou mais).
- Cada alerta é enviado uma vez e é rearmado quando a situação normaliza.
- Criar (Modo Maestro, uma vez por projeto), com **um comando**:
  ```bash
  python <projeto>/.claude/skills/monitor-uso/uso.py sentinela [--intervalo 120] [--limite 75]
  maestri check "Sentinela"
  ```
  O subcomando descobre o terminal do maestro (linha após "You:" em `maestri list`), grava `sentinela-alvo.txt` e recruta o Sentinela (se já existir, recria com `--replace`). Use `MAESTRI_CLI` se `maestri` não estiver no PATH. A primeira linha do `maestri check` diz quem ele avisa.

## Ao receber um alerta
1. Rode `uso.py status`.
2. **Família perto do limite:**
   - não inicie tarefas longas nela; passe o próximo trabalho para outra família, todas de primeira linha (`brain/orquestracao.md`);
   - se a tarefa em andamento não puder mudar de família, aplique a skill `agendar-retomada` (checkpoint + rotina no reset).
3. **Se o próprio maestro (Claude) estiver acima de 85%:**
   - grave o checkpoint em `brain/status.md`;
   - delegue o restante ao Codex ou ao Gemini (o que tiver folga) com instruções completas;
   - agende a retomada.
4. **Desequilíbrio:** nas próximas delegações, priorize a família com mais folga, inclusive nos campos em que ela é "alternativa" na tabela de modelos.
