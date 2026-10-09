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

## .claude/settings.json (base de modelos do projeto)
```json
{
  "model": "sonnet",
  "advisorModel": "opus",
  "env": { "CLAUDE_CODE_SUBAGENT_MODEL": "haiku" }
}
```
Se o projeto já tiver um `settings.json`, acrescente essas chaves sem apagar as existentes.

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
| Claude | Sonnet | maestro e recrutas: dirige e constrói | `--preset "Claude Code" --command "claude --model sonnet --advisor opus --add-dir <projeto>"` |
| Claude | Haiku | subagentes de exploração (paralelos, só leitura) | `CLAUDE_CODE_SUBAGENT_MODEL=haiku` (via `.claude/settings.json`) |
| Claude | Opus | assessor (advisor): plano, erro repetido, conferência final | `--advisor opus` / `advisorModel` |
| GPT (Codex) | gpt-6.1-sol (medium) | dirige e constrói: backend, algoritmos | `--preset "Codex" --command "codex -m gpt-6.1-sol -s workspace-write --add-dir <projeto>"` |
| GPT (Codex) | gpt-6-luna (low) | subagente `explorador`; testes e mecânico | papel `explorador` (`~/.codex/agents/explorador.toml`) |
| GPT (Codex) | gpt-6.1-sol (xhigh) | subagente `revisor`: plano, erro repetido, conferência final | papel `revisor` (`~/.codex/agents/revisor.toml`) |
| GPT (Codex) | ~~gpt-6-astra~~ | **não usar** | — |
| Gemini (Antigravity) | gemini-3.8-flash-high | dirige e constrói: backend isolado, relatórios, documentação | `--preset "Antigravity" --command "agy --model gemini-3.8-flash-high --mode accept-edits --add-dir <projeto>"` (sem `agy` no PATH, use `C:/Users/<user>/.gemini/bin/agy.exe`) |
| Gemini (Antigravity) | gemini-3.8-flash-low | explora; testes e mecânico | mesmo comando, com `--model gemini-3.8-flash-low` |
| Gemini (Antigravity) | gemini-3.1-pro-high | revisa (não edita) | mesmo comando, com `--model gemini-3.1-pro-high` |

## Configuração base Claude, Codex e Gemini
- Claude: Sonnet constrói, Haiku explora, Opus revisa (assessor). Configurado em `.claude/settings.json`; o Opus só entra para revisar planos, desbloquear erros repetidos e fazer a conferência final.
- Codex: gpt-6.1-sol constrói, `explorador` (gpt-6-luna) explora, `revisor` (gpt-6.1-sol xhigh) revisa. Nunca gpt-6-astra. Os papéis vêm do `instalar.sh`; os prompts dizem quando chamá-los.
- Gemini (Antigravity): flash-high constrói, flash-low explora, pro-high revisa. Não há papéis de subagente: o prompt pede "explore antes de editar" e "faça uma revisão crítica antes de concluir". O grupo "Claude and GPT models" do Antigravity tem cota própria e serve de reserva quando a assinatura Claude estiver no limite.

## Que modelo para cada campo
<tabela campo → primário / alternativa / esforço>

## Equilíbrio de uso Claude × Codex × Gemini
- **Objetivo:** usar as três assinaturas de forma equivalente e nunca parar à força por limite.
- **Antes de delegar:** rode `python .claude/skills/monitor-uso/uso.py status`.
  - Se `preferir: codex`, use gpt-6.1-sol/gpt-6-luna também nos campos em que o Claude é o primário: app, análise, documentação.
  - Se `preferir: gemini`, use gemini-3.8-flash nesses mesmos campos.
  - Se `preferir: claude`, o inverso.
- Tarefas de implementação vão de preferência para a **família com mais folga** (Codex ou Gemini). O maestro (Claude) fica com orquestração, decisões e integração, para poupar a própria cota.
- Maestro acima de 85%: checkpoint no `status.md`, o restante vai para o Codex ou o Gemini com instruções completas e a retomada é agendada.
- **Sentinela** (terminal Shell, sem custo de modelo; criado por `uso.py sentinela`) avisa o maestro em 75% de qualquer das três famílias ou em desequilíbrio de 35 pontos ou mais. Skill: `monitor-uso`.
- Limite atingido: realocar; senão, checkpoint + `agendar-retomada`. Tarefa longa: rede de segurança antes.

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

## .claude/skills/monitor-uso/ e .claude/skills/agendar-retomada/
Não reescreva: copie os arquivos completos desta skill.
- `skills-base/monitor-uso/SKILL.md` + `scripts/uso.py` → `.claude/skills/monitor-uso/`
- `skills-base/agendar-retomada/SKILL.md` → `.claude/skills/agendar-retomada/`
- Coloque `.claude/skills/monitor-uso/sentinela-alvo.txt` no `.gitignore`. O arquivo é criado por `python .claude/skills/monitor-uso/uso.py sentinela` (com o nome do terminal do maestro, linha após "You:" de `maestri list`), que também recruta o Sentinela.

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
