# Prompt: criar um projeto do zero com a governança maestro

Abra o Claude Code numa **pasta vazia** (de preferência dentro do canvas Maestri, no terminal do maestro) e cole o bloco abaixo. Preencha os `<...>` se já souber as respostas. Os que você deixar em branco, o Claude pergunta, tudo numa rodada só.

---

```text
Vamos criar um projeto novo do zero nesta pasta vazia, com a governança da skill `governanca-maestro`.

## Projeto
- Nome: <nome>
- O que é e para quem: <1-3 linhas>
- Documento de escopo (opcional): <caminho ou "nenhum">
- Stack desejada: <stack ou "você propõe">
- Regras não negociáveis: <ex.: banco X é somente leitura; LGPD; dados pessoais nunca saem do servidor>
- Idioma das notas e respostas: <pt-BR>

## Passo 0: garantir a skill
1. Se a skill `governanca-maestro` estiver disponível, invoque-a e siga a seção 11 (Bootstrap).
2. Se não estiver, instale-a a partir do repositório `C:/Users/zkozt/Projetos/governanca-maestro` (`cp -r governanca-maestro ~/.claude/skills/`), leia o `SKILL.md` de lá e siga a mesma seção.
Leia só as seções de `referencias/modelos.md` que for usar.

## Passo 1: entrevista curta (uma rodada só)
Antes de criar os arquivos, pergunte de uma vez só o que faltar acima e o que for decisão minha:
- os objetivos da primeira entrega;
- os usuários e perfis;
- as integrações e fontes de dados (e se são somente leitura);
- onde vai rodar;
- os modelos e assinaturas disponíveis (Claude, Codex, Gemini);
- se uso o canvas Maestri;
- o nível de autonomia.
O resto você decide e registra.

## Passo 2: estrutura (bootstrap)
1. `git init -b main`, `.gitignore` (incluindo `.env`, `dados-locais/`, artefatos de teste), `.env.example` e `.githooks/pre-commit` com `git config core.hooksPath .githooks`.
2. `brain/` como camada de informações e armazenamento:
   - notas-base: README, status, diario, inbox, perguntas-abertas, glossario, roadmap, orquestracao, decisoes/README + _modelo;
   - notas de domínio destiladas da entrevista e do escopo: visao, requisitos, arquitetura;
   - frontmatter (`resumo`, `tags`, `aliases`) em todas, com links `[[ ]]`.
3. Skills-base em `.claude/skills/`:
   - `brain-search` (com `grafo.py` e o vocabulário de tags deste projeto);
   - `monitor-uso` (com `uso.py`);
   - `agendar-retomada`;
   - se houver recurso sensível (banco de produção, API paga), uma skill de acesso único e controlado, com travas testadas.
4. `CLAUDE.md` curto, com as regras não negociáveis e ponteiros para o brain.
5. Memória do usuário: salve as preferências de autonomia e idioma, se ainda não existirem.
6. ADR 0001 com a stack, ou a proposta dela marcada como "Proposta" se depender de mim.
7. `roadmap.md` com as etapas e a primeira entrega bem definida.
8. `orquestracao.md` com os modelos disponíveis, a tabela de modelo por área de trabalho e os papéis que serão necessários.

## Passo 3: verificar e registrar
- Rode `python .claude/skills/brain-search/grafo.py checar` até dar 0 problemas.
- Teste `grafo.py busca` com 2 termos do projeto e `uso.py status`.
- Teste o hook: tente fazer commit de um `.env` falso e confirme o bloqueio. Depois apague o arquivo.
- Faça o commit inicial ("Bootstrap: governança, brain, skills-base").
- Registre a sessão no `diario.md` e os próximos passos no `status.md`.

## Passo 4: time (só se eu usar o Maestri)
- Rode `maestri list` e crie os papéis necessários para a PRIMEIRA tarefa do roadmap (não o time inteiro).
- Crie a nota "Quadro do Projeto" e suba a Sentinela (terminal Shell com `uso.py vigiar`).
- Não recrute ninguém para trabalho que ainda não existe.

## Regras desta sessão
- Siga a governança: o maestro decide e integra; o mais barato que resolve; nada entra sem verificação; tudo que for durável vai para o brain no momento em que surgir.
- Confirme comigo só o que for destrutivo ou externo (push, criação de repositório remoto, instalação global além da skill).
- Ao final, me dê um relatório curto: estrutura criada, decisões tomadas (com ADRs), perguntas em aberto e a primeira tarefa sugerida, com o agente e o modelo para ela.
```

---

## Dicas
- **Com um documento de escopo:** coloque o arquivo na pasta antes de começar e informe o caminho. O Claude destila o conteúdo em notas e cita o original, sem copiá-lo.
- **Sem o Maestri:** o passo 4 é pulado e a delegação usa subagentes do Claude Code. A governança continua igual.
- **Depois do bootstrap:** para começar a primeira entrega, basta pedir "siga o roadmap". O Claude lê o `status.md`, escolhe a próxima tarefa e delega.
