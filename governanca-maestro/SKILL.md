---
name: governanca-maestro
description: Metodologia de governança para projetos de software orquestrados por IA. Claude é o maestro e delega a agentes Claude/Codex/Gemini (canvas Maestri ou subagentes). Cobre o segundo cérebro em brain/ como camada de informações e armazenamento (o que fica onde, protocolos de leitura e escrita, ciclo de vida, busca em grafo), a escolha de modelo por custo, a economia de tokens, os limites de uso e a retomada agendada, a criação de skills, ADRs, commits verificados e regras não negociáveis. Use ao INICIAR um projeto novo ("monte a estrutura", "aplique a governança", "bootstrap"), ao organizar o trabalho com agentes, ou quando o usuário perguntar como o processo funciona.
---

# governanca-maestro: método para projetos orquestrados por IA

Esta skill não trata do conteúdo de nenhum projeto. Ela define **como** um projeto é conduzido: quem decide, onde fica o conhecimento, quem executa, quanto isso custa e como o trabalho sobrevive a limites de uso e trocas de sessão.

Arquivos desta skill:
- `scripts/grafo.py`: busca em grafo no `brain/`. Python 3 puro, sem dependências.
- `scripts/uso.py`: limites de uso do Claude (estimado) e do Codex (exato).
- `referencias/modelos.md`: modelos prontos de cada arquivo (CLAUDE.md, notas, skills, hook). Leia só a seção que for usar.

## 1. Princípios
1. **Maestro e orquestra.** A sessão principal (o modelo mais capaz) planeja, decide, delega, revisa e integra. Quem executa são agentes mais baratos e especializados.
2. **Fonte única de contexto: `brain/`.** É a camada de informações e armazenamento do projeto: todo agente consulta o brain antes de agir e grava nele o que descobre. Nenhum conhecimento depende da memória de uma conversa (seção 3).
3. **Custo mínimo suficiente.** Use o modelo e o esforço mais baratos que resolvem bem a tarefa. Só suba de nível quando ela exigir ou quando a tentativa barata falhar.
4. **Diversidade na revisão.** Quem implementa nunca revisa o próprio trabalho. A revisão é de preferência cruzada entre famílias (Claude ↔ GPT).
5. **Nada entra sem verificação.** Typecheck, testes ou execução real antes de dar algo como pronto. Commit só com tudo verde.
6. **Procedimento repetível vira skill.** Quando algo é feito pela segunda vez, empacote.
7. **Autonomia com limites claros.** Decisões técnicas e commits locais não precisam de pedido. Confirme antes de qualquer coisa destrutiva ou externa (push, deploy, envio, exclusão, escrita em sistemas de terceiros).
8. **O trabalho sobrevive a interrupções.** Checkpoint no `status.md` e retomada agendada quando um limite aparece.

## 2. Estrutura de um projeto
```
CLAUDE.md                  # regras do projeto + ponteiros (curto; carregado em toda sessão)
brain/                     # segundo cérebro (Obsidian-compatível)
  README.md                # índice das notas
  status.md                # onde estamos (lido no início de TODA sessão)
  diario.md                # log cronológico das sessões
  inbox.md                 # captura rápida
  perguntas-abertas.md     # dúvidas pendentes / respondidas
  glossario.md             # termos
  roadmap.md               # etapas
  orquestracao.md          # time, modelos, roles, notas do canvas, lições
  visao.md, requisitos.md, arquitetura.md, ...   # conteúdo do projeto
  decisoes/                # ADRs: README.md (índice), _modelo.md, 0001-*.md
.claude/skills/<nome>/     # skills do projeto (versionadas): SKILL.md + scripts
.githooks/pre-commit       # bloqueia segredos e artefatos (core.hooksPath)
dados-locais/              # dados brutos e extrações (no .gitignore; o brain guarda só o resumo)
```
O que fica em cada lugar (memória do usuário, brain, código, canvas, dados): veja a seção 3.1.

## 3. Segundo cérebro: camada de informações e armazenamento
O `brain/` é a **memória externa do projeto**. Ele fica entre as fontes (usuário, documentos, bancos, código) e quem trabalha (maestro, recrutas, sessões futuras).
- **Como camada de informação**, é o lugar onde todo agente consulta o que já se sabe antes de agir.
- **Como armazenamento**, é o lugar onde todo resultado durável é gravado assim que surge.

Com isso, o conhecimento fica separado de qualquer conversa, modelo ou ferramenta: troca de sessão, compactação de contexto, limite de uso ou troca de agente não apagam nada. É texto puro (Markdown), versionado no git, compatível com o Obsidian e lido por qualquer modelo.

### 3.1 Mapa de armazenamento: cada informação em uma camada
| Camada | Guarda | Vida útil | Quem lê |
|---|---|---|---|
| `CLAUDE.md` | regras não negociáveis + ponteiros para o brain | permanente; curto | toda sessão (carga automática) |
| Memória do usuário | preferências de trabalho e perfil do usuário | entre projetos | o maestro |
| **`brain/`** | **conhecimento do projeto**: domínio, decisões, estado, dúvidas, lições | permanente, versionado | todos, via busca |
| Código + git | a implementação e o histórico de mudanças | permanente | quem implementa |
| `.claude/skills/` | procedimentos executáveis (como fazer) | permanente, versionado | todos, via gatilho |
| Notas do canvas | coordenação viva (tarefas, achados de revisão) | enquanto durar a rodada | agentes conectados |
| `dados-locais/` (fora do git) | dados brutos, extrações, CSVs | descartável/regenerável | scripts |
| Scratchpad / temp | rascunhos, saídas intermediárias | a sessão | quem criou |

Regras de fronteira:
- **O brain não duplica o código nem o git.** Ele registra o *porquê*, o *estado* e o *que se sabe*. O *como está feito* é o código, e o *quando mudou* é o git. Aponte para arquivos e commits em vez de copiá-los.
- **Dados brutos nunca vão para o brain.** Ele guarda o resumo (números agregados, perfil, regras de limpeza), a origem, a data da extração e o caminho do script que a regenera.
- **Nada de segredos nem dados pessoais no brain**, porque ele é versionado e lido por todos os agentes. Use só agregados ou dados pseudonimizados.
- **O efêmero converge para o brain.** Ao fim de cada rodada, as notas do canvas, os relatórios dos agentes e as conclusões de subagentes são consolidados pelo maestro numa nota ou no diário.

### 3.2 Tipos de nota
| Tipo | Exemplos | Regra de escrita |
|---|---|---|
| Índice (hub) | `README.md`, `decisoes/README.md` | uma linha por nota; toda nota nova entra aqui |
| Estado | `status.md` | sobrescrito; curto e atual (feito / em andamento / próximos / bloqueios) |
| Registro | `diario.md`, ADRs | só acréscimo. Um ADR não se edita: é **substituído** por outro ADR, que aponta para ele |
| Fila | `inbox.md`, `perguntas-abertas.md` | os itens entram, são processados e saem (para uma nota ou para "Respondidas") |
| Referência | `glossario.md`, `orquestracao.md`, dados/fontes | consolidado; atualize a seção em vez de acrescentar uma nova |
| Domínio | visão, requisitos, arquitetura, indicadores... | uma ideia por `##`; dividir quando passar de ~150 linhas ou misturar assuntos |

### 3.3 Convenções (o que torna a busca possível)
- Frontmatter em toda nota: `resumo` (uma linha, que entra na busca e no `mapa`), `tags` (minúsculas, sem acento, de um **vocabulário controlado** listado na skill brain-search; amplie o vocabulário lá antes de usar uma tag nova) e `aliases` (sinônimos que o usuário usaria).
- Uma ideia por seção `##`, com título descritivo: a busca pesa o título e devolve a seção como unidade de leitura.
- Links `[[nota]]` ou `[[pasta/nota]]`, com pelo menos um backlink por nota. O grafo é o que permite expandir o contexto sem ler tudo.
- Fatos com **origem e data** ("medido em 2026-10-06 via `consulta.py`", "decidido pelo usuário em ..."). Datas sempre absolutas, nunca "ontem".
- Arquivos que começam com `_` são modelos e ficam fora do grafo.

### 3.4 Protocolo de leitura (camada de informação)
1. **Início de sessão:** `status.md` e mais nada.
2. **Precisa de algo:** `grafo.py busca "<2-4 termos>"` devolve as seções com intervalo `L<ini>-<fim>`. Leia **só esse intervalo** (`Read` com offset/limit).
3. **Faltou contexto:** `grafo.py vizinhos <nota>` mostra links, backlinks e tags em comum. Leia a seção vizinha mais relevante. Para uma visão geral barata: `grafo.py mapa`.
4. **Não achou:** a informação não existe. Pergunte ao usuário ou investigue, e **grave o resultado** (passo 3.5) antes de seguir.
5. **Agentes recebem ponteiros, não cópias:** "leia `brain/dados.md` L40-62". Recrutas também usam `grafo.py`. Quando a ferramenta não alcança o brain (sandbox), copie o trecho para um arquivo na pasta do role.

### 3.5 Protocolo de escrita (armazenamento)
Grave **no momento em que a informação surge**, não no fim da sessão: uma sessão pode cair a qualquer momento.

| Gatilho | Destino |
|---|---|
| Ideia ou informação ainda sem lugar | `inbox.md` |
| Decisão técnica ou de produto | novo ADR (copie `decisoes/_modelo.md`) + índice; reflita na nota de domínio afetada |
| Resposta do usuário a uma dúvida | mova o item para "Respondidas" em `perguntas-abertas.md` **e** atualize a nota afetada |
| Dúvida que depende do usuário ou do cliente | `perguntas-abertas.md`, por criticidade, com a nota afetada |
| Descoberta sobre dados, sistemas ou domínio (medição, perfil, regra) | a nota de domínio correspondente, com origem e data |
| Termo novo | `glossario.md` |
| Resultado de agente (revisão, análise, auditoria) | conclusões na nota de domínio ou em `orquestracao.md`; detalhes de achados podem ficar na nota do canvas até a rodada fechar |
| Armadilha de ferramenta ou processo | `orquestracao.md` → "Lições" (se repetir, vira skill) |
| Checkpoint antes de limite ou tarefa longa | `status.md` → `## Retomada agendada` |
| Fim de sessão ou de bloco | `status.md` (sobrescrever) + `diario.md` (acrescentar: data, bullets, links, hashes de commit) |

Depois de qualquer escrita: `grafo.py checar` até 0 problemas. Commit das notas junto com o código da rodada (ou um commit "Brain: ...").

### 3.6 Ciclo de vida da informação
```
inbox ──────────────► nota de domínio
pergunta-aberta ────► respondida ──► nota de domínio / ADR
nota do canvas ─────► (fim da rodada) ──► nota de domínio / diário
status (estado) ────► (substituído) ──► diário (histórico)
lição ──────────────► orquestracao.md ──► (2ª ocorrência) skill
documento de escopo ► destilado em visao / requisitos / arquitetura (original citado, não copiado)
```

### 3.7 Manutenção
- **Fim de sessão:** esvazie o inbox, enxugue o `status.md` (o que saiu vai para o diário) e rode `checar`.
- **Nota grande ou misturada:** divida em notas atômicas, mantendo os links, e atualize o índice.
- **Informação desatualizada:** corrija na fonte e não acrescente uma contradição. Quando o histórico importar, registre a mudança no diário ou num novo ADR.
- Não leia o brain inteiro para "se atualizar": isso anula o propósito da camada.

## 4. Orquestração
**Ferramentas, em ordem de preferência**
1. **Canvas Maestri** (skills `maestri-manager`, `maestri`, `maestri-routines`, `maestri-workspace`, `maestri-portal`). Agentes visíveis e persistentes, notas compartilhadas, floors (git worktree), portais de navegador/dispositivo e rotinas.
2. **Subagentes internos do Claude Code** (`Agent`, com `model: haiku|sonnet|opus`). Só para buscas rápidas e descartáveis.
3. **O próprio maestro.** Não delegue o que você resolve em 1 ou 2 comandos: delegar também custa (inicialização e contexto).

**Recrutar**
- Rode sempre `maestri list` antes e **reaproveite** quem já existe: o contexto dele já está pago.
- Defina um **role** por função (escopo de pastas + o que pode e o que não pode fazer) e um **codinome** curto por agente.
- **Sempre dê ao recruta o diretório do projeto** (`--add-dir <projeto>`; no Codex também `-s workspace-write`). Sem isso, o recruta fica preso na pasta do role.
- Roles típicos: Dev Backend, Dev App/Front, Dev Testes (E2E), Revisor de Código (não edita), Designer UI/UX, Revisor de Design (não edita), Sentinela (Shell, sem modelo).

**Que modelo para cada campo** (ajuste a tabela de `orquestracao.md` aos modelos disponíveis)
| Campo | Primário | Alternativa | Esforço |
|---|---|---|---|
| Arquitetura, ADRs, integração, decisões | maestro (Opus) | GPT forte (2ª opinião) | médio; alto só se crítico |
| Backend / algoritmos | GPT forte (Codex) | Sonnet | médio / alto |
| Front / app / UI | Sonnet | GPT forte, Gemini | médio |
| Análise de dados, SQL, relatórios | Sonnet | GPT leve | médio |
| Testes, refatoração mecânica | GPT leve | Haiku | baixo / médio |
| Revisão de código e segurança | família **oposta** à do autor | — | médio / alto |
| Documentação, notas, resumos | Haiku | GPT leve | baixo |
| Busca descartável | subagente Haiku | — | baixo |

**Delegar bem**
- O prompt é curto e autocontido: objetivo, escopo de arquivos, restrições, critério de pronto e formato da resposta ("responda em até N linhas: arquivos alterados, testes, dúvidas").
- Cite **só** as seções do brain necessárias (caminho + linhas), nunca "leia o brain".
- Tarefas independentes vão em paralelo (`maestri ask --batch`). Tarefas que mexem nos mesmos arquivos vão em sequência ou em floors separados.
- Contratos compartilhados (tipos, schemas) são escritos **antes** pelo maestro e só então distribuídos. Assim backend e front trabalham em paralelo sem colidir.
- Achados de revisão vão para uma **nota do canvas** ("Revisao <área>") conectada ao autor, que marca cada item como `[corrigido]`, `[backlog]` ou `[não procede]`.

**Ciclo de entrega que funciona**
contrato → implementação em paralelo → verificação do maestro (typecheck/testes) → revisão cruzada → correções → E2E → conferência visual (se houver UI) → commit da rodada → brain atualizado.

## 5. Economia de tokens
- `status.md` no início; depois disso, **só busca no grafo + leitura por intervalo**.
- `CLAUDE.md` curto: regras e ponteiros, sem conteúdo que já está no brain.
- Saídas longas de comandos: filtre (`tail`, `grep`, `--reporter=dot`) ou mande para um arquivo e leia o trecho. Atenção: **nunca** use pipe dentro da condição de um commit (veja a seção 8).
- Prefira reaproveitar um recruta a criar outro, e recrutar a carregar tudo no contexto do maestro.
- O maestro (o modelo mais caro) fica com o que exige julgamento. Implementação, testes e documentação vão para modelos mais baratos.
- Respostas dos agentes: concisas por contrato do prompt. Relatórios ao usuário: curtos, com o que foi feito, o que foi verificado e o que falta.
- Skills com divulgação progressiva: um `SKILL.md` enxuto e os detalhes em `referencias/`, lidos só quando necessários.
- Ao esperar um agente, use um laço de verificação com intervalo (ou um aviso de conclusão) em vez de checar a toda hora.

## 6. Limites de uso e continuidade
- **Equilíbrio entre assinaturas.** Antes de distribuir trabalho, rode `python .claude/skills/monitor-uso/uso.py status`. Se ele disser `preferir: X`, use a família X também nos campos em que ela é só a alternativa. A meta é usar as duas cotas de forma parecida e nunca parar à força.
- **Sentinela.** Um terminal Shell, sem custo de modelo, roda `uso.py vigiar --intervalo 120 --limite 75 --avisar "<terminal do maestro>"` e avisa em 75% de uso ou em desequilíbrio de 35 pontos ou mais.
- **Limite atingido (reativo):**
  1. Realoque a tarefa para outro modelo disponível.
  2. Se não der, grave o checkpoint em `## Retomada agendada` no `status.md` (tarefa, feito, próximo passo exato, agentes e resets, rotina).
  3. Agende uma rotina `--once` para o **maior** reset entre os agentes necessários + 5 min, com um comando que **verifica antes de agir**.
- **Tarefa longa (preventivo):** o maestro não enxerga a própria cota. Antes de começar, crie a rotina `Rede: <tarefa>` (agora + 5 h 10 min) com checkpoint. Ao terminar, **desative** a rotina e limpe a seção.
- Rotinas são desativadas, nunca apagadas sem pedido do usuário. Antes de criar, rode `maestri routine list` para não duplicar.
- **"Pare tudo":** deixe terminar o que está em execução, verifique, faça o commit, desative as rotinas, atualize status e diário e não comece nada novo.

## 7. Criação de skills
**Quando:** um procedimento se repete, tem armadilhas ou precisa de trava (por exemplo, acesso a dados sensíveis).

**Anatomia:** `.claude/skills/<nome-kebab>/SKILL.md` + scripts opcionais + `referencias/` opcional.
- Frontmatter: `name` e `description`. A description diz **o que** a skill faz e **quando usar**, com os gatilhos literais (mensagens de erro, palavras do usuário, momentos do fluxo como "ANTES de…" e "depois de…"). É ela que faz a skill disparar.
- Corpo: um fluxo numerado e imperativo, os comandos exatos, as tabelas de decisão e "o que fazer quando der errado". Nada de teoria.
- Scripts: determinísticos, sem dependências quando possível, rodados a partir da raiz do projeto, com saída curta e legível (o modelo vai ler essa saída).
- **Padrão "porta única"** para recursos perigosos (banco de produção, API paga, credenciais): a skill é o **único** caminho permitido, com travas em camadas (usuário só leitura + validação da consulta + transação read-only), sem nunca mostrar segredos nem dados pessoais. Teste a trava com tentativas reais de escrita.
- Revise a skill com outro modelo antes de confiar nela.
- Registre a skill na tabela "Skills do projeto" em `orquestracao.md` (nome, para quê, status) e, se for genérica, promova para `~/.claude/skills/`.
- Skills externas (oficiais de frameworks): instale em `.claude/skills/`, mantenha a LICENSE e registre a origem.

## 8. Qualidade, segurança e git
- Commit só assim: `typecheck && test && git commit`. **Sem pipe no meio da condição**: um `| grep` engole a falha.
- Testes lentos ou instáveis em paralelo: registre no status e rode em série para validar. Não ignore.
- Hook versionado (`.githooks/pre-commit` + `git config core.hooksPath .githooks`) que bloqueia `.env`, chaves, dados locais e artefatos de teste.
- Uma rodada = um commit com mensagem descritiva do que mudou e do que ainda falta ("ainda sem revisão/E2E").
- As **regras não negociáveis** do projeto (segurança, privacidade, somente leitura, UX essencial) ficam no `CLAUDE.md` e são repetidas nos prompts de quem toca a área.
- LGPD e privacidade desde o início: cada perfil vê só o necessário; logs e relatórios só com agregados.

## 9. Comunicação com o usuário
- Idioma e tom do usuário. Relatórios curtos: feito, verificado, pendente e riscos.
- Pergunte só o que for decisão dele. O resto decida, registre (ADR ou diário) e siga.
- Dúvidas que bloqueiam vão para `perguntas-abertas.md` e são agrupadas numa única pergunta ao usuário.
- No modo autopiloto: escolha a próxima frente pelo roadmap, avise em uma linha e siga com rede de segurança ativa.

## 10. Lições operacionais (Maestri, Codex, Claude Code)
- Prompts longos no Codex podem ficar parados na caixa de entrada. Depois do `ask`, confira com `maestri check` e, se preciso, envie Enter com `maestri ask "<Nome>" --raw "\n"`.
- O sandbox do Codex não tem o CLI `maestri`. Para passar uma nota a ele, copie o conteúdo para um arquivo na pasta do role.
- Aprovações de comandos do Codex fora do sandbox: aprove **uma vez** (`--raw "y"`), só depois de conferir o comando. Nunca escolha "não perguntar de novo".
- Terminais Windows/PowerShell: evite aspas aninhadas no `--command` e use `.cmd` em vez de `.ps1` para CLIs npm.
- As cotas são compartilhadas entre o maestro e os recrutas da mesma família.
- Processos em segundo plano do maestro (servidores) param no tempo limite; para servidores de dev, use o máximo.
- Revisão visual: confira o DOM e a tela realmente servidos, não só o código (caches de bundler enganam).

## 11. Bootstrap de um projeto novo
Execute na raiz do projeto, adaptando os modelos de `referencias/modelos.md`:
1. `git init` (se preciso), `.gitignore` e `.githooks/pre-commit` + `git config core.hooksPath .githooks`.
2. Crie o `brain/` (camada de informações, seção 3) com as notas-base (README, status, diario, inbox, perguntas-abertas, glossario, roadmap, orquestracao, decisoes/README + _modelo). Se houver um documento de escopo, destile-o em visao/requisitos/arquitetura.
3. Copie as skills-base para `.claude/skills/`:
   - `brain-search/` (SKILL.md do modelo + `scripts/grafo.py` desta skill);
   - `monitor-uso/` (SKILL.md + `scripts/uso.py`);
   - `agendar-retomada/` (SKILL.md);
   - ajuste o vocabulário de tags na brain-search.
4. Escreva o `CLAUDE.md` do modelo, com as regras não negociáveis do projeto.
5. Salve na memória do usuário as preferências de autonomia e idioma, se ainda não existirem.
6. Rode `grafo.py checar` até zerar os problemas e faça o commit inicial.
7. Se houver Maestri: `maestri list`, crie os roles, recrute só o necessário para a primeira tarefa, crie a nota "Quadro do Projeto" e suba a Sentinela.
8. Registre a sessão no `diario.md` e os próximos passos no `status.md`.
