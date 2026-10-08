# Criar um projeto do zero com a governança maestro

## Jeito curto (com o `instalar.sh` já rodado nesta máquina)
Abra o Claude Code numa **pasta vazia** (de preferência no terminal do maestro, no canvas Maestri) e mande:

```text
siga o repo para definir a estrutura base e governança do projeto
```

O Claude vai, nesta ordem:
1. **Montar a estrutura** sem perguntar nada: git, hook, `brain/`, skills-base e `CLAUDE.md`. Depois verifica e faz o commit.
2. **Entrar direto no planejamento:** faz perguntas em blocos curtos (problema, usuários, primeira entrega, dados, restrições, regras e forma de trabalho) e grava cada resposta no `brain/` na hora.
3. **Apresentar o plano consolidado e pedir sua aprovação.** Só depois disso ele monta o time e começa a Etapa 1.

Se tiver um documento de escopo, imagens ou planilhas, coloque-os na pasta antes de mandar, ou envie durante o planejamento. O Claude lê, destila no brain e pula as perguntas que já estiverem respondidas.

## Jeito completo (máquina sem a skill, ou para já adiantar respostas)
Cole o bloco abaixo e preencha o que já souber. O que ficar em branco vira pergunta no planejamento.

```text
Siga o repo https://github.com/Cozta1/governanca-maestro para definir a estrutura base e governança deste projeto, nesta pasta.

1. Se a skill `governanca-maestro` não estiver instalada: clone o repo numa pasta temporária e rode `sh instalar.sh`. O repo é privado; se o clone pedir login, me peça para rodar `! git clone ...`.
2. Siga a seção 11 do SKILL.md (estrutura base, sem perguntas) e, logo depois, a seção 12 (planejamento comigo, roteiro em referencias/planejamento.md).

O que já sei do projeto (use e não me pergunte de novo):
- Nome: <nome>
- O que é e para quem: <1-3 linhas>
- Documento de escopo: <caminho ou "nenhum">
- Stack: <stack ou "você propõe">
- Regras não negociáveis: <...>
- Modelos disponíveis / Maestri: <...>
- Idioma: <pt-BR>

Confirme comigo só o que for destrutivo ou externo. Nada de implementação antes de eu aprovar o plano.
```
