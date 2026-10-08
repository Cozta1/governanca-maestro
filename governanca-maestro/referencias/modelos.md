# Modelos de arquivos (governanca-maestro)

Substitua `<...>`. Leia só a seção que for usar.

## CLAUDE.md
```markdown
# Projeto: <nome>

<uma linha: o que o sistema faz e para quem>
Escopo original: `<documento>`. Stack: <resumo> (ver `brain/decisoes/0001-*.md`).

## Segundo cérebro (`brain/`): base de informações do projeto
- **No início da sessão:** leia `brain/status.md`.
- **Para qualquer outra informação:** use a skill `brain-search` (`python .claude/skills/brain-search/grafo.py busca "<termos>"`) e leia só as linhas indicadas. Não leia as notas inteiras.
- **Convenções:** toda nota tem frontmatter (`resumo`, `tags`, `aliases`) e links `[[nota]]`; uma ideia por seção `##`; depois de editar, rode `grafo.py checar` até zerar os problemas.
- **Onde registrar:** ideia solta → `brain/inbox.md`; decisão → novo ADR em `brain/decisoes/` (copie `_modelo.md`) + índice; dúvida → `brain/perguntas-abertas.md`; termo → `brain/glossario.md`; fim de sessão → `brain/status.md` e `brain/diario.md`.

## Orquestração (ver `brain/orquestracao.md`)
- Você é o **maestro**: planeja, delega, revisa e integra.
- Crie agentes **de preferência no canvas Maestri**, com o modelo adequado; subagentes internos só para buscas descartáveis.
- Antes de recrutar, rode sempre `maestri list` e reaproveite quem já existe.
- Use o modelo e o esforço mais baratos que resolvem a tarefa (tabela em `orquestracao.md`).
- Procedimento repetível vira skill em `.claude/skills/`, registrada em `orquestracao.md`.
- Limite de uso ou tarefa longa: use a skill `agendar-retomada`.

## Regras do projeto (não negociáveis)
- <regra de segurança/dados>
- <regra de privacidade>
- <regra de UX essencial>

Idioma: <idioma>.
```

## brain/README.md
```markdown
---
resumo: Índice do segundo cérebro e como buscar nele
tags: [projeto, processo]
aliases: [indice, index]
---
# Segundo Cérebro: <projeto>

## Como buscar (skill brain-search)
- `python .claude/skills/brain-search/grafo.py busca "<termos>"`: seções relevantes, com linhas.
- `... vizinhos <nota>` · `... mapa` · `... checar`.

## Notas
| Nota | Para quê |
|---|---|
| [[status]] | Onde estamos agora e próximos passos |
| [[roadmap]] | Etapas |
| [[orquestracao]] | Agentes, modelos, skills, lições |
| [[perguntas-abertas]] | Dúvidas a resolver |
| [[glossario]] | Termos |
| [[decisoes/README]] | ADRs |
| [[inbox]] | Captura rápida |
| [[diario]] | Log de sessões |
```

## brain/status.md
```markdown
---
resumo: Situação atual do projeto, próximos passos e bloqueios (ler no início de cada sessão)
tags: [projeto, roadmap]
aliases: [situacao, onde paramos]
---
# Status

**Fase atual:** <etapa> ([[roadmap]])
**Atualizado:** <AAAA-MM-DD>

## Feito
- ...

## Em andamento
- ...

## Próximos passos
1. ...

## Bloqueios
- Nenhum.

<!-- Seção temporária, criada pela skill agendar-retomada:
## Retomada agendada
- Tarefa / Feito até agora / Próximo passo exato / Agentes e resets / Rotina -->
```

## brain/diario.md, inbox.md, glossario.md, roadmap.md
```markdown
---
resumo: Log cronológico das sessões de trabalho
tags: [processo]
aliases: [log]
---
# Diário

## <AAAA-MM-DD>
- <o que foi feito, com [[links]] e hashes de commit>
```
- O `inbox.md` tem o mesmo frontmatter (`resumo: Captura rápida...`) e uma lista vazia; aponte para [[README]].
- O `glossario.md` é uma lista com `**Termo**: definição`.
- O `roadmap.md` tem uma seção `##` por etapa, com checklist.

## brain/perguntas-abertas.md
```markdown
---
resumo: Dúvidas pendentes, agrupadas por criticidade, cada uma com a nota afetada
tags: [projeto]
aliases: [duvidas, pendencias]
---
# Perguntas abertas

## Críticas (bloqueiam a etapa atual)
- [ ] <pergunta> → [[nota-afetada]]

## Importantes
- [ ] ...

## Respondidas
- [x] <pergunta>: <resposta> (<data>) → [[nota]]
```

## brain/orquestracao.md
```markdown
---
resumo: Como o desenvolvimento é orquestrado: maestro, agentes, modelos, roles, skills e lições
tags: [orquestracao, processo]
aliases: [maestro, agentes, time]
---
# Orquestração do desenvolvimento

## Princípio
O Claude Code é o maestro: planeja, delega, revisa e integra. O `brain/` é a fonte única de contexto.

## Modelos disponíveis
| Família | Modelo | Perfil | Como recrutar |
|---|---|---|---|
| Claude | Opus | maestro | — |
| Claude | Sonnet | código, UI, análise | `--preset "Claude Code" --command "claude --model sonnet --add-dir <projeto>"` |
| Claude | Haiku | barato | `--command "claude --model haiku --add-dir <projeto>"` |
| GPT (Codex) | <forte> | backend, revisão | `--preset "Codex" --command "codex -m <modelo> -s workspace-write --add-dir <projeto>"` |
| GPT (Codex) | <leve> | testes, mecânico | idem, com o modelo leve |

## Que modelo para cada campo
<tabela campo → primário / alternativa / esforço>

## Equilíbrio de uso
Antes de delegar, rode `uso.py status`; siga o `preferir:`. A Sentinela avisa em 75% ou em desequilíbrio ≥ 35 pontos.

## Roles criados
| Role | Escopo | Usado por |
|---|---|---|

## Canvas: notas
| Nota | Para quê | Conectada a |
|---|---|---|
| Quadro do Projeto | time, tarefas, regras | todos |

## Regras
1. Recrutar só com paralelismo real ou para uma segunda opinião; reaproveitar recrutas.
2. A tarefa delegada cita as notas relevantes e pede resultado conciso.
3. O maestro revisa e integra; nada entra sem verificação.
4. Conhecimento novo → nota; procedimento repetível → skill.
5. Commit só com typecheck e testes verdes, sem pipe na condição.
6. Limite de modelo: realocar; senão, checkpoint + retomada agendada.

## Skills do projeto
| Skill | Para quê | Status |
|---|---|---|
| `brain-search` | busca em grafo no brain | pronta |
| `monitor-uso` | limites e equilíbrio de uso | pronta |
| `agendar-retomada` | checkpoint + rotina depois do limite | pronta |

## Lições
- <data>: <armadilha encontrada e regra que veio dela>

Relacionadas: [[status]], [[roadmap]].
```

## brain/decisoes/README.md e _modelo.md
```markdown
---
resumo: Índice das decisões de arquitetura (ADRs)
tags: [decisao]
aliases: [adrs]
---
# Decisões
| # | Decisão | Status |
|---|---|---|
| [[decisoes/0001-<slug>]] | <título> | Aceita |
```
```markdown
---
resumo: <uma linha com a decisão>
tags: [decisao]
status: Proposta
---
# NNNN: Título da decisão

**Data:** AAAA-MM-DD
**Status:** Proposta | Aceita | Substituída por NNNN

## Contexto
## Opções consideradas
## Decisão
## Consequências
```

## .claude/skills/brain-search/SKILL.md
Copie `scripts/grafo.py` desta skill para `.claude/skills/brain-search/grafo.py`.
```markdown
---
name: brain-search
description: Busca em grafo no segundo cérebro (brain/) do projeto <nome>. Use ANTES de ler qualquer nota de brain/ e sempre que precisar de informação do projeto (<temas principais>). Também use depois de criar ou editar notas, para checar o grafo.
---

# brain-search
Não leia as notas inteiras. Script: `python .claude/skills/brain-search/grafo.py <comando>` (rode a partir da raiz).

1. `busca "<termos>"` (`--max 5`, `--prof 1`): seções com `L<ini>-<fim>`, linhas de match e vizinhos.
2. Leia só o trecho (`Read` com offset/limit).
3. Se faltar contexto, use `vizinhos <nota>`. Para uma visão geral, `mapa`.
4. Depois de editar, rode `checar` até ter 0 problemas.

Dicas: 2 a 4 termos. A busca ignora acentos e maiúsculas.

## Convenções
Frontmatter `resumo` / `tags` / `aliases`. Vocabulário de tags: <lista>. Links `[[nota]]` e pelo menos um backlink. Uma ideia por `##`. Arquivos `_*.md` são ignorados.
```

## .claude/skills/monitor-uso/SKILL.md
Copie `scripts/uso.py` para `.claude/skills/monitor-uso/uso.py`.
```markdown
---
name: monitor-uso
description: Consulta os limites de uso do Claude (estimado) e do Codex (exato) para decidir para qual família delegar e evitar paradas forçadas. Use antes de distribuir tarefas, quando a Sentinela avisar, ou quando o usuário perguntar sobre limites.
---

# monitor-uso
`python .claude/skills/monitor-uso/uso.py <status|json|vigiar>`
- Codex: lê `rate_limits` de `~/.codex/sessions`; o valor é exato.
- Claude: estima pelos tokens ponderados em `~/.claude/projects` (janela de 5 h), calibrado pelo último 429.
- A saída traz `preferir: codex|claude|equilibrado`.

Sentinela: terminal Shell com `uso.py vigiar --intervalo 120 --limite 75 --avisar "<terminal do maestro>"`.

Ao receber um alerta:
1. Rode `status`.
2. Se uma família estiver perto do limite, mande o próximo trabalho para a outra.
3. Se a tarefa não puder mudar de família, use `agendar-retomada`.
4. Se o maestro passar de 85%: faça o checkpoint, delegue o restante e agende a retomada.
```

## .claude/skills/agendar-retomada/SKILL.md
```markdown
---
name: agendar-retomada
description: Agenda ações futuras do projeto, em especial a continuação de uma tarefa quando um modelo atinge o limite de uso, usando rotinas do Maestri. Use quando aparecer "usage limit", "rate limit", "quota exceeded", 429, RESOURCE_EXHAUSTED, "try again in", "limit will reset at"; quando o usuário avisar do limite; e ANTES de tarefas longas ou lotes de delegação.
---

# agendar-retomada
1. **Detectar:** leia a saída dos recrutas com `maestri check "<Nome>"` e anote o horário de reset, se houver.
2. **Realocar, se der:** outro modelo disponível assume a tarefa agora.
3. **Checkpoint** em `brain/status.md` → `## Retomada agendada`: tarefa, feito, próximo passo exato, agentes e resets, rotina.
4. **Horário:** o maior reset + 5 min. Se for desconhecido, use 1 h (Codex/Gemini) ou 5 h (Claude), registrado como estimativa.
5. **Agendar:** rode `maestri routine list` e depois:
   `maestri routine create "Retomar: <tarefa>" --once "<AAAA-MM-DD HH:mm>" --command "Retomada agendada: leia 'Retomada agendada' em brain/status.md e continue do próximo passo. Verifique antes se ainda está pendente."`
   (para um recruta, use `--terminal "<Nome>"`; o maestro agenda depois dele.) Avise o usuário.
6. **Preventivo:** antes de uma tarefa longa, crie `Rede: <tarefa>` em agora + 5 h 10 min. Ao concluir, `maestri routine disable` (nunca delete sem pedido) e limpe a seção.
7. **Ao retomar:** confira o estado real, continue, limpe a seção e registre no diário.
```

## Skill "porta única" (recurso sensível)
```markdown
---
name: <recurso>-leitura
description: Única forma de acessar <recurso> em modo SOMENTE LEITURA. Use para <casos>. Nunca acesse <recurso> de outra forma.
---
# <recurso>-leitura
- Credenciais só em `.env` (fora do git); nunca imprima segredos nem dados pessoais.
- Travas: (1) usuário com permissão mínima; (2) o script aceita só SELECT/SHOW/DESCRIBE, com uma instrução por chamada; (3) sessão/transação read-only.
- Uso: `python .claude/skills/<recurso>-leitura/consulta.py "<SELECT ...>"` com limite de linhas.
- Saída agregada ou pseudonimizada. Extrações vão para uma pasta ignorada pelo git.
```

## .githooks/pre-commit
```sh
#!/bin/sh
# Bloqueia arquivos que nunca podem ir para o git (credenciais, dados locais, artefatos de teste).
proibidos=$(git diff --cached --name-only --diff-filter=ACMR | grep -E '(^|/)\.env$|(^|/)\.env\.(local|dev|prod|producao)$|(^|/)dados-locais/|(^|/)test-results/|(^|/)playwright-report/|\.pem$|\.key$')
if [ -n "$proibidos" ]; then
  echo "pre-commit: arquivos proibidos no commit:" >&2
  echo "$proibidos" >&2
  exit 1
fi
```
Ative com `git config core.hooksPath .githooks`. A lista explícita de sufixos deixa passar o `.env.example`, que deve ser versionado.

## Memória do usuário (preferências, não fatos do projeto)
- `autonomia`: commits e decisões técnicas sem pedir; confirmar só o que for destrutivo ou externo.
- `orquestracao`: delegar via Maestri; salvar procedimentos como skills.
- `perfil`: idioma, domínio técnico do usuário.
