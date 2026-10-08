# Planejamento: roteiro da entrevista e formato do plano

O objetivo é sair da conversa com um **plano aprovado** e com o `brain/` preenchido. O usuário fala sobre o problema; o maestro traduz isso em escopo, requisitos e decisões.

## Como conduzir
- Faça **blocos de 3 a 5 perguntas** por vez, nunca um questionário inteiro. Quando houver escolhas típicas, use perguntas de múltipla escolha (AskUserQuestion) com a recomendação primeiro. Para o que for aberto, faça perguntas abertas.
- **Pule o que já foi respondido** (pelo documento de escopo, pelo código existente ou por respostas anteriores). Confirme o que você inferiu em vez de perguntar de novo.
- **Grave no brain a cada bloco**, sem deixar para o fim:
  - respostas → nota de domínio;
  - termos → glossário;
  - decisão aceita → ADR;
  - o que ficou sem resposta → `perguntas-abertas.md`.
- Depois de cada bloco, faça um **resumo de 2 ou 3 linhas** do que entendeu antes de passar ao próximo, para o usuário poder corrigir.
- O usuário pode responder "você decide": nesse caso, decida, registre como ADR ou no diário e siga.
- O usuário pode mandar arquivos (documentos, imagens, planilhas, prints): leia, destile no brain e cite o original.
- Se o projeto for pequeno, comprima os blocos. O plano tem de caber no problema.

## Blocos
### 1. Problema e objetivo → `visao.md`
- Que problema o projeto resolve, e para quem? Como isso é feito hoje?
- Como saberemos que deu certo (métricas, prazos, o que muda no dia a dia)?
- Que perguntas o sistema precisa responder, ou que trabalho ele precisa eliminar?

### 2. Usuários e fluxos → `requisitos.md`
- Quem usa (perfis) e o que cada perfil precisa fazer? Qual é o fluxo principal de cada um?
- Em que dispositivos e em que contexto (no celular, na rua, no escritório, offline)?
- O que cada perfil **não** pode ver ou fazer (permissões, privacidade)?

### 3. Escopo da primeira entrega → `roadmap.md`
- Qual é o menor recorte que já entrega valor de verdade (MVP)?
- O que fica explicitamente **fora** da primeira entrega?
- Há prazo, data de demonstração ou dependência externa?

### 4. Dados e integrações → `arquitetura.md` (e uma nota `dados.md`, se houver)
- De onde vêm os dados (sistemas existentes, bancos, planilhas, APIs)? Algum acesso é só leitura?
- Que dados são sensíveis (pessoais, financeiros, de saúde)? Há exigências de LGPD ou de compliance?
- Há histórico disponível para analisar antes de construir?

### 5. Restrições e infraestrutura → ADRs
- Onde vai rodar (nuvem, servidor próprio, lojas de apps)? Há orçamento ou custo mensal máximo?
- Há stack obrigatória, ou proibida, ou alguma preferência do time?
- Quem mantém o sistema depois?
→ Proponha stack, arquitetura e hospedagem com **uma recomendação e alternativas curtas**. Cada decisão aceita vira um ADR.

### 6. Regras não negociáveis → `CLAUDE.md`
- O que nunca pode acontecer (escrever no banco de produção, expor dado pessoal, quebrar o fluxo X)?
- Como deve ser a experiência essencial, a que não pode ficar complicada?

### 7. Forma de trabalho → `orquestracao.md` e memória do usuário
- Que modelos e assinaturas estão disponíveis (Claude, Codex, Gemini)? Vamos usar o Maestri?
- Que nível de autonomia: commits e decisões técnicas sem pedir? O que precisa de confirmação?
- Onde fica o repositório remoto (se houver) e quem revisa?

## Plano consolidado (apresentar para aprovação)
Apresente em uma única mensagem curta:
1. **Visão:** uma frase sobre o problema e para quem, e o critério de sucesso.
2. **Primeira entrega:** o que entra, o que fica de fora e o prazo.
3. **Requisitos principais:** por perfil, em bullets.
4. **Decisões:** stack, arquitetura e hospedagem, com os links dos ADRs.
5. **Regras não negociáveis.**
6. **Riscos e perguntas abertas**, cada um com o que bloqueia.
7. **Roadmap:** etapas, cada uma com um objetivo verificável.
8. **Primeira tarefa:** o que é, quem faz (agente e modelo) e como verificar.

Termine com: "Aprova o plano? Posso ajustar qualquer item antes de começarmos."

Na aprovação, o `status.md` passa para "Fase atual: Etapa 1" e o diário registra "Plano aprovado em <data>". Depois disso, siga a seção 12 do `SKILL.md`.
