---
name: vigia-recrutas
description: Aprova, uma vez e só quando for seguro, os pedidos de confirmação de comandos dos recrutas Codex (sandbox) e Antigravity/agy ("Requesting permission for:") enquanto o maestro faz outra coisa. Use ao delegar lotes longos a recrutas Codex ou agy que ficam parados esperando aprovação, ou quando `maestri check` mostrar "Press enter to confirm" ou "Requesting permission for:".
---

# vigia-recrutas: aprovações seguras em segundo plano

Recrutas Codex (com sandbox) e Antigravity pedem confirmação para comandos. Sem vigia, o trabalho para até o maestro olhar. O `vigia.sh` faz o laço: lê `maestri check`, aprova **uma vez** só o que é claramente seguro e **para** em qualquer outro caso.

## Procedimento
1. Copie `vigia.sh` desta skill para o scratchpad do maestro (fora do repositório do projeto).
2. Rode em segundo plano, a partir da pasta onde quer o `vigia.log`, com os recrutas e o formato de cada um:
   ```bash
   MAESTRI_CLI=<caminho do maestri, se não estiver no PATH> bash vigia.sh -i 5 Backend:codex Front:agy &
   ```
3. Acompanhe só o `vigia.log` (`tail -n 5 vigia.log`). Uma linha `PARAR: ...` significa que um pedido não foi aprovado: leia a tela com `maestri check "<Nome>"`, decida você mesmo e reinicie o vigia.
4. Ao terminar o lote, mate o processo do vigia.

## O que ele faz
| Formato | Marca na tela | Aprovação enviada |
|---|---|---|
| `:codex` | "Press enter to confirm" | `maestri ask "<Nome>" --raw "y"` |
| `:agy` | "Requesting permission for:" | Enter (opção 1) |

## O que ele aprova (só comandos locais seguros)
- leitura: `ls`, `cat`, `head`, `tail`, `grep`, `rg`, `wc`, `cd`;
- `pnpm`/`npm`/`yarn`: `install`, `test`, `typecheck`, `lint`, `build`; `vitest`, `tsc`, `eslint`;
- `docker compose ps` e `docker compose logs`;
- `git status`, `diff`, `log`, `show`, `add`, `commit`.

Comandos encadeados com `&&`, `||`, `;` ou `|` só passam se **cada trecho** passar.

## Quando ele PARA (e avisa no log)
- `git push`, `reset`, `clean`, `rebase`, `--force`;
- exclusões (`rm`, `Remove-Item`, `-delete`), downloads (`curl`, `wget`), instalação global (`-g`);
- recriar o banco (`docker compose down/up`, `down -v`, `migrate reset`, `DROP`);
- leitura de `.env`, redirecionamentos (`>`), substituição de comandos;
- qualquer comando que ele não consiga ler da tela ou que não esteja na lista;
- o mesmo comando pedido de novo logo após a aprovação (algo travou).

## Regras
- **Nunca** escolha "não perguntar de novo" nem use `--dangerously-skip-permissions`.
- Para ampliar a lista de comandos seguros, edite `SEGURO` no `vigia.sh` e revise a mudança com outra família antes de usar.
- O formato da tela muda entre versões do Codex e do agy: se o vigia não reconhecer um pedido, ele não aprova. Ajuste `pendente()` e `extrair()` conferindo a saída real de `maestri check`.
- Os recrutas Codex não têm o CLI `maestri`; o vigia roda no terminal do maestro, não no do recruta.
