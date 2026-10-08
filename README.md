# governanca-maestro

Skill do Claude Code com uma metodologia de governança para projetos de software orquestrados por IA:
- o Claude atua como maestro e delega a agentes Claude, Codex e Gemini;
- o `brain/` funciona como camada de informações e armazenamento;
- os modelos são escolhidos pelo custo, com economia de tokens;
- os limites de uso são monitorados e o trabalho é retomado por agendamento;
- procedimentos repetidos viram skills;
- commits só entram verificados.

Todo projeto começa com **estrutura base → plano aprovado → execução**.

## Conteúdo
```
instalar.sh                  # instala/atualiza a skill + atalho no ~/.claude/CLAUDE.md
PROMPT-NOVO-PROJETO.md       # como começar um projeto do zero
governanca-maestro/
├── SKILL.md                 # o guia (carregado pelo Claude Code)
├── referencias/
│   ├── modelos.md           # CLAUDE.md, notas do brain, skills-base, hook
│   └── planejamento.md      # roteiro da entrevista e formato do plano
└── scripts/
    ├── grafo.py             # busca em grafo no brain/ (Python 3, sem dependências)
    └── uso.py               # limites de uso Claude (estimado) × Codex (exato)
```

## Instalar (uma vez por máquina)
```sh
git clone https://github.com/Cozta1/governanca-maestro.git
cd governanca-maestro && sh instalar.sh
```
O script copia a skill para `~/.claude/skills/` e adiciona ao `~/.claude/CLAUDE.md` um atalho que vale em todas as sessões.

## Usar
Numa pasta vazia (ou num projeto existente), mande:
```text
siga o repo para definir a estrutura base e governança do projeto
```
O Claude monta a estrutura, entra direto no planejamento com você e só começa a executar depois que você aprovar o plano. Detalhes e a versão longa do prompt estão em [`PROMPT-NOVO-PROJETO.md`](PROMPT-NOVO-PROJETO.md).

## Atualizar
Edite neste repositório, faça o commit e o push, e rode `sh instalar.sh` de novo. Melhorias descobertas num projeto (lições, regras novas) voltam para cá.
