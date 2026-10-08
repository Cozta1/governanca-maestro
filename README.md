# governanca-maestro

Skill do Claude Code com uma metodologia de governança para projetos de software orquestrados por IA. O Claude atua como maestro e delega a agentes Claude, Codex e Gemini. O `brain/` funciona como camada de informações e armazenamento. A skill também cobre a escolha de modelo por custo, a economia de tokens, os limites de uso com retomada agendada, a criação de skills e os commits verificados.

## Conteúdo
```
governanca-maestro/
├── SKILL.md               # o guia (carregado pelo Claude Code)
├── referencias/modelos.md # modelos de CLAUDE.md, notas do brain, skills-base e hook
└── scripts/
    ├── grafo.py           # busca em grafo no brain/ (Python 3, sem dependências)
    └── uso.py             # limites de uso Claude (estimado) × Codex (exato)
```

## Instalar
Para o seu usuário (vale em todos os projetos):
```sh
cp -r governanca-maestro ~/.claude/skills/
```
Para um projeto só (versionada junto com ele):
```sh
cp -r governanca-maestro <projeto>/.claude/skills/
```

## Usar
Num projeto, peça "aplique a governança neste projeto" ou rode `/governanca-maestro`. O Claude segue o checklist de bootstrap (seção 11 do `SKILL.md`): cria o `brain/`, as skills-base, o `CLAUDE.md` e o hook de pre-commit.

## Projeto novo a partir de uma pasta vazia
Use o prompt pronto em [`PROMPT-NOVO-PROJETO.md`](PROMPT-NOVO-PROJETO.md): abra o Claude Code na pasta vazia, cole o bloco e preencha os campos.

## Atualizar
Edite neste repositório, faça o commit e reinstale com o `cp` acima. Melhorias descobertas num projeto (lições, regras novas) voltam para cá.
