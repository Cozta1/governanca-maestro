#!/usr/bin/env python3
"""Busca em grafo no segundo cérebro (brain/).

Nós = notas .md; arestas = links [[nota]] (saída + backlinks). Tags em comum são
mostradas em `vizinhos`, mas não entram no ranking (tags genéricas gerariam ruído).
Sem índice persistido: tudo é parseado a cada chamada, então nunca fica desatualizado.

Uso:
  grafo.py busca "<termos>" [--max 5] [--prof 1]
  grafo.py vizinhos <nota>
  grafo.py mapa
  grafo.py checar
"""
import argparse
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

STOPWORDS = set(
    "a o os as um uma uns umas de da do das dos e ou em no na nos nas ao aos "
    "para pra por pelo pela com sem que se como mais menos ja nao sim ser ter "
    "eh e sao foi esta este essa esse isso isto qual quais quando onde quem "
    "seu sua seus suas meu minha nosso nossa ate sobre entre cada".split()
)
LINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]")
HEAD_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
CERCA_RE = re.compile(r"^\s*(```|~~~)")
CODIGO_INLINE_RE = re.compile(r"(`+).*?\1")

PESO_SECAO = 4     # título da seção
TETO_CORPO = 3     # ocorrências no corpo contam até este teto
PESO_NOTA = 5      # título da nota, id, alias ou tag (reforço)
PESO_RESUMO = 3    # resumo do frontmatter (reforço)
FATOR_META = 0.5   # reforço dos metadados só vale para termos com match local
FATOR_VIZINHO = 0.3


def normalizar(texto):
    texto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in texto if not unicodedata.combining(c)).lower()


def tokens(texto):
    return [t for t in re.findall(r"[a-z0-9]+", normalizar(texto)) if t not in STOPWORDS and (len(t) > 1 or t.isdigit())]


def radical(t):
    # Stemming barato: "notificacao" e "notificacoes" compartilham "notificac".
    return t[:-2] if len(t) > 6 else t


def casa(termo, palavra):
    if len(termo) < 4:
        return palavra == termo
    return palavra.startswith(radical(termo))


def ocorrencias(termo, contagem):
    return sum(n for palavra, n in contagem.items() if casa(termo, palavra))


class Secao:
    def __init__(self, titulo, ini):
        self.titulo, self.ini, self.fim, self.linhas = titulo, ini, ini, []


class Nota:
    def __init__(self, id_, caminho):
        self.id, self.caminho = id_, caminho
        self.meta, self.secoes, self.links_brutos = {}, [], []
        self.titulo = id_
        self.saida = set()
        self.quebrados = []

    @property
    def resumo(self):
        return self.meta.get("resumo", "")

    @property
    def tags(self):
        return lista(self.meta.get("tags", []))

    @property
    def aliases(self):
        return lista(self.meta.get("aliases", []))


def lista(v):
    return v if isinstance(v, list) else ([v] if v else [])


def valor_escalar(v):
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "'\"":
        return v[1:-1]
    return v


def lista_inline(v):
    # "[a, 'b, c', d]" -> ["a", "b, c", "d"], respeitando aspas
    itens = re.findall(r"""\s*("[^"]*"|'[^']*'|[^,]+)\s*(?:,|$)""", v[1:-1])
    return [valor_escalar(i) for i in itens if i.strip()]


def ler_frontmatter(linhas):
    """Subconjunto de YAML: `chave: valor`, `chave: [a, b]` e listas em bloco (`- item`)."""
    if not linhas or linhas[0].strip() != "---":
        return {}, 0
    meta, chave = {}, None
    for i in range(1, len(linhas)):
        linha = linhas[i].rstrip()
        if linha.strip() == "---":
            return meta, i + 1
        item = re.match(r"^\s*-\s+(.*)$", linha)
        if item and chave:
            if not isinstance(meta.get(chave), list):
                meta[chave] = []
            meta[chave].append(valor_escalar(item.group(1)))
        elif ":" in linha and not linha.startswith((" ", "\t")):
            chave, valor = linha.split(":", 1)
            chave, valor = chave.strip(), valor.strip()
            meta[chave] = lista_inline(valor) if valor.startswith("[") and valor.endswith("]") else valor_escalar(valor)
    return {}, 0  # frontmatter sem fechamento: ignora


def carregar_nota(id_, caminho):
    nota = Nota(id_, caminho)
    linhas = caminho.read_text(encoding="utf-8").splitlines()
    nota.meta, inicio = ler_frontmatter(linhas)
    atual = Secao("(topo)", inicio + 1)
    cerca = None  # "```" ou "~~~" quando dentro de bloco de código
    for i in range(inicio, len(linhas)):
        linha = linhas[i]
        c = CERCA_RE.match(linha)
        if c and (cerca is None or c.group(1) == cerca):
            cerca = None if cerca else c.group(1)
        m = None if cerca or c else HEAD_RE.match(linha)
        if m:
            if atual.titulo != "(topo)" or any(l.strip() for l in atual.linhas):
                nota.secoes.append(atual)
            atual = Secao(m.group(2), i + 1)
            if m.group(1) == "#" and nota.titulo == id_:
                nota.titulo = m.group(2)
        atual.linhas.append(linha)
        atual.fim = i + 1
        if not cerca and not c:
            nota.links_brutos += LINK_RE.findall(CODIGO_INLINE_RE.sub("", linha))
    nota.secoes.append(atual)
    return nota


def achar_brain(arg):
    if arg:
        brain = Path(arg).resolve()
        if not brain.is_dir():
            sys.exit(f"--brain: diretório não existe: {brain}")
        return brain
    for base in [Path(__file__).resolve().parent, *Path(__file__).resolve().parents, Path.cwd()]:
        if (base / "brain").is_dir():
            return base / "brain"
    sys.exit("brain/ não encontrado; use --brain <dir>")


def carregar(brain):
    notas, ilegiveis = {}, []
    for caminho in sorted(brain.rglob("*.md")):
        if caminho.name.startswith("_"):
            continue
        id_ = caminho.relative_to(brain).with_suffix("").as_posix()
        try:
            notas[id_] = carregar_nota(id_, caminho)
        except (OSError, UnicodeDecodeError) as e:
            ilegiveis.append(id_)
            print(f"aviso: não consegui ler {caminho}: {e}", file=sys.stderr)
    if not notas:
        sys.exit(f"nenhuma nota .md em {brain}")
    for nota in notas.values():
        for bruto in nota.links_brutos:
            alvo = resolver(bruto, notas, origem=nota.id)
            if alvo:
                if alvo != nota.id:
                    nota.saida.add(alvo)
            elif bruto not in nota.quebrados:
                nota.quebrados.append(bruto)
    return notas, ilegiveis


def resolver(nome, notas, origem=None):
    chave = nome.strip().casefold()
    if chave.endswith(".md"):
        chave = chave[:-3]
    ids = {id_.casefold(): id_ for id_ in notas}
    # 1) relativo à pasta da nota de origem; 2) caminho a partir de brain/
    if origem and "/" in origem:
        relativo = f"{origem.rsplit('/', 1)[0]}/{chave}".casefold()
        if relativo in ids:
            return ids[relativo]
    if chave in ids:
        return ids[chave]
    por_nome = [id_ for id_ in notas if id_.rsplit("/", 1)[-1].casefold() == chave]
    if len(por_nome) == 1:
        return por_nome[0]
    por_alias = [n.id for n in notas.values() if chave in (a.casefold() for a in n.aliases)]
    return por_alias[0] if len(por_alias) == 1 else None


def entradas(notas):
    ent = {id_: set() for id_ in notas}
    for nota in notas.values():
        for alvo in nota.saida:
            ent[alvo].add(nota.id)
    return ent


def vizinhos_fortes(id_, notas, ent):
    return notas[id_].saida | ent[id_]


def mesmas_tags(id_, notas):
    def norm_tags(n):
        return {normalizar(t) for t in n.tags}
    tags = norm_tags(notas[id_])
    return {o: sorted(tags & norm_tags(n)) for o, n in notas.items() if o != id_ and tags & norm_tags(n)}


def rel(nota):
    return nota.caminho.relative_to(nota.caminho.parents[len(Path(nota.id).parts)]).as_posix()


# ---------- comandos ----------

def cmd_busca(notas, consulta, maximo, prof):
    termos = list(dict.fromkeys(tokens(consulta)))
    if not termos:
        sys.exit("consulta vazia")
    ent = entradas(notas)
    resultados = {}  # id -> [(score, secao, termos_casados, linhas_match)]
    for nota in notas.values():
        cab_nota = Counter(tokens(" ".join([nota.id.replace("/", " "), nota.titulo, *nota.tags, *nota.aliases])))
        cont_resumo = Counter(tokens(nota.resumo))
        for sec in nota.secoes:
            corpo = "\n".join(sec.linhas[1:] if sec.titulo != "(topo)" else sec.linhas)
            if not corpo.strip():
                continue  # seção só com título (ex.: H1 seguido de ##): nada para ler
            cont_titulo = Counter(tokens(sec.titulo))
            cont_corpo = Counter(tokens(corpo))
            score, casados = 0.0, []
            for t in termos:
                # Só conta termo com match local (título da seção ou corpo); os metadados
                # da nota apenas reforçam, senão toda seção da nota apareceria.
                local = PESO_SECAO * bool(ocorrencias(t, cont_titulo)) + min(ocorrencias(t, cont_corpo), TETO_CORPO)
                if local:
                    meta = PESO_NOTA * bool(ocorrencias(t, cab_nota)) + PESO_RESUMO * bool(ocorrencias(t, cont_resumo))
                    score += local + FATOR_META * meta
                    casados.append(t)
            if not score:
                continue
            score *= 0.5 + 0.5 * len(casados) / len(termos)
            linhas_match = [sec.ini + i for i, l in enumerate(sec.linhas)
                            if any(casa(t, p) for t in casados for p in tokens(l))][:6]
            resultados.setdefault(nota.id, []).append([score, sec, casados, linhas_match])

    melhor = {id_: max(r[0] for r in rs) for id_, rs in resultados.items()}
    for id_, rs in resultados.items():
        alcance, fronteira = set(), {id_}
        for _ in range(prof):
            fronteira = {v for f in fronteira for v in vizinhos_fortes(f, notas, ent)} - alcance - {id_}
            alcance |= fronteira
        bonus = FATOR_VIZINHO * max((melhor.get(v, 0) for v in alcance), default=0)
        for r in rs:
            r[0] += bonus

    ordem = sorted(resultados, key=lambda i: -max(r[0] for r in resultados[i]))[:maximo]
    print(f"busca: {' '.join(termos)}")
    if not ordem:
        print("nenhum resultado — tente `mapa` ou outros termos")
        return
    for pos, id_ in enumerate(ordem, 1):
        nota = notas[id_]
        tags = f"  [{', '.join(nota.tags)}]" if nota.tags else ""
        print(f"\n{pos}. {id_}  ({rel(nota)}){tags}")
        if nota.resumo:
            print(f"   {nota.resumo}")
        for score, sec, casados, lm in sorted(resultados[id_], key=lambda r: -r[0])[:2]:
            print(f"   § {sec.titulo}  L{sec.ini}-{sec.fim}  score {score:.1f}  termos: {', '.join(casados)}"
                  + (f"  linhas: {', '.join(map(str, lm))}" if lm else ""))
        viz = sorted(vizinhos_fortes(id_, notas, ent))
        if viz:
            print(f"   ↳ vizinhos: {', '.join(viz)}")


def cmd_vizinhos(notas, nome):
    id_ = resolver(nome, notas)
    if not id_:
        sys.exit(f"nota '{nome}' não encontrada")
    ent = entradas(notas)
    nota = notas[id_]
    print(f"{id_}  ({rel(nota)})  {nota.resumo}")
    print(f"→ links de saída: {', '.join(sorted(nota.saida)) or '-'}")
    print(f"← backlinks: {', '.join(sorted(ent[id_])) or '-'}")
    tags = mesmas_tags(id_, notas)
    print("# mesmas tags: " + (", ".join(f"{o} ({'/'.join(t)})" for o, t in sorted(tags.items())) or "-"))
    print("seções: " + "; ".join(f"{s.titulo} L{s.ini}-{s.fim}" for s in nota.secoes))


def cmd_mapa(notas):
    for nota in notas.values():
        tags = f" [{', '.join(nota.tags)}]" if nota.tags else ""
        links = f" → {', '.join(sorted(nota.saida))}" if nota.saida else ""
        print(f"{nota.id} — {nota.resumo or '(sem resumo)'}{tags}{links}")


def cmd_checar(notas, ilegiveis):
    ent = entradas(notas)
    problemas = len(ilegiveis)
    for id_ in ilegiveis:
        print(f"ilegível (não carregada): {id_}")
    for nota in notas.values():
        for q in nota.quebrados:
            print(f"link quebrado: {nota.id} → [[{q}]]")
            problemas += 1
        if not nota.resumo:
            print(f"sem resumo: {nota.id}")
            problemas += 1
        if not ent[nota.id] and nota.id.rsplit("/", 1)[-1] != "README":
            print(f"órfã (sem backlinks): {nota.id}")
            problemas += 1
    print(f"{len(notas)} notas, {sum(len(n.saida) for n in notas.values())} links, {problemas} problema(s)")
    return 1 if problemas else 0


def main():
    p = argparse.ArgumentParser(description="Busca em grafo no segundo cérebro")
    p.add_argument("--brain", help="diretório do brain (padrão: procura brain/ acima do script)")
    sub = p.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("busca")
    b.add_argument("termos", nargs="+")
    b.add_argument("--max", type=int, default=5)
    b.add_argument("--prof", type=int, default=1)
    v = sub.add_parser("vizinhos")
    v.add_argument("nota")
    sub.add_parser("mapa")
    sub.add_parser("checar")
    args = p.parse_args()

    notas, ilegiveis = carregar(achar_brain(args.brain))
    if args.cmd == "busca":
        cmd_busca(notas, " ".join(args.termos), args.max, args.prof)
    elif args.cmd == "vizinhos":
        cmd_vizinhos(notas, args.nota)
    elif args.cmd == "mapa":
        cmd_mapa(notas)
    else:
        sys.exit(cmd_checar(notas, ilegiveis))


if __name__ == "__main__":
    main()
