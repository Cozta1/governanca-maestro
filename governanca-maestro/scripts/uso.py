#!/usr/bin/env python3
"""Monitor de limites de uso das três famílias: Codex (exato, dos logs), Claude (exato pela API de uso
da Anthropic, a mesma do /usage; estimado e calibrado só se a API falhar) e Gemini (exato, pelo
comando `agy -p /usage` do Antigravity).

Codex grava `rate_limits` (used_percent, resets_at) nos rollouts em ~/.codex/sessions.
Claude só grava tokens por mensagem e o registro `quotaLimits` quando um limite estoura (429);
a estimativa soma o consumo ponderado da janela de 5 h atual e divide pelo consumo que causou
a última rejeição registrada (calibração). Sem rejeição registrada, mostra só o consumo.
As três famílias entram nos alertas e na recomendação `preferir: claude|codex|gemini|equilibrado`.

Uso:
  uso.py status                     # resumo legível
  uso.py json                       # resumo em JSON
  uso.py vigiar [--intervalo 120] [--limite 75] [--avisar "<terminal do maestro>"]
  uso.py sentinela [--intervalo 120] [--limite 75]   # cria/recria o terminal Sentinela no Maestri

O painel do `vigiar` mostra barras coloridas por família (verde < 50%, amarelo < 75%, vermelho >= 75%),
horários de reinício em dd/mm e os últimos alertas.

Sem --avisar, o vigia avisa o terminal escrito em sentinela-alvo.txt (ao lado deste script),
ou "Claude Code Maestro" se o arquivo não existir. Assim o comando do Sentinela não precisa de aspas.
O subcomando `sentinela` descobre o terminal do maestro (linha após "You:" em `maestri list`),
grava sentinela-alvo.txt e recruta (ou recria, com --replace) o terminal "Sentinela" já com o `vigiar`.
"""
import argparse
import glob
import json
import os
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timedelta, timezone

sys.stdout.reconfigure(encoding="utf-8")

CASA = os.path.expanduser("~")
JANELA = timedelta(hours=5)
# Peso relativo aproximado ao custo (entrada = 1).
PESOS = {"input_tokens": 1.0, "cache_creation_input_tokens": 1.25, "cache_read_input_tokens": 0.1, "output_tokens": 5.0}


def agora():
    return datetime.now(timezone.utc)


def ler_jsonl(caminho):
    try:
        with open(caminho, encoding="utf-8", errors="ignore") as f:
            for linha in f:
                linha = linha.strip()
                if linha:
                    try:
                        yield json.loads(linha)
                    except json.JSONDecodeError:
                        continue
    except OSError:
        return


# ---------------- Codex ----------------

def uso_codex():
    """Evento `token_count` mais recente (pelo timestamp do evento, não pela data do arquivo).

    Sessões longas (ex.: Codex desktop) acumulam eventos de vários dias num arquivo só; o arquivo
    modificado por último pode ter como último evento de limite um registro antigo.
    """
    arquivos = sorted(glob.glob(os.path.join(CASA, ".codex", "sessions", "*", "*", "*", "*.jsonl")), key=os.path.getmtime, reverse=True)
    melhor = None  # (timestamp, rate_limits)
    for arq in arquivos[:8]:
        with open(arq, encoding="utf-8", errors="ignore") as f:
            for linha in f:
                if '"token_count"' not in linha or '"rate_limits"' not in linha:
                    continue
                try:
                    reg = json.loads(linha)
                except json.JSONDecodeError:
                    continue
                payload = reg.get("payload") or {}
                rl = payload.get("rate_limits") if payload.get("type") == "token_count" else None
                ts = reg.get("timestamp")
                # Evento sem `resets_at` na janela de 5 h (comum quando o limite já estourou) não informa o uso.
                if rl and not (rl.get("primary") or {}).get("resets_at"):
                    continue
                if rl and ts and (melhor is None or ts > melhor[0]):
                    melhor = (ts, rl)
    if not melhor:
        return {"fonte": "indisponivel"}
    rl = melhor[1]
    p, s = rl.get("primary") or {}, rl.get("secondary") or {}
    agora_ts = agora().timestamp()
    # Janela já reiniciada desde o último evento: uso efetivo é 0.
    pct = lambda j: 0.0 if (j.get("resets_at") or 0) < agora_ts else j.get("used_percent")
    return {
        "fonte": "exato",
        "janela5h_pct": pct(p),
        "janela5h_reset": iso(p.get("resets_at")),
        "semana_pct": pct(s),
        "semana_reset": iso(s.get("resets_at")),
        "visto_em": datetime.fromisoformat(melhor[0].replace("Z", "+00:00")).astimezone().strftime("%Y-%m-%d %H:%M"),
    }


def buscar_chave(obj, chave):
    if isinstance(obj, dict):
        if chave in obj:
            return obj[chave]
        for v in obj.values():
            r = buscar_chave(v, chave)
            if r is not None:
                return r
    elif isinstance(obj, list):
        for v in obj:
            r = buscar_chave(v, chave)
            if r is not None:
                return r
    return None


def iso(ts):
    if ts is None:
        return None
    if isinstance(ts, str) and not ts.replace(".", "", 1).isdigit():
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone().strftime("%Y-%m-%d %H:%M")
    return datetime.fromtimestamp(float(ts), timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M")


# ---------------- Antigravity (Gemini) ----------------

AGY = os.environ.get("AGY_CLI") or os.path.join(CASA, ".gemini", "bin", "agy.exe" if os.name == "nt" else "agy")
CACHE_CLAUDE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache-claude.json")
CACHE_AGY = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache-antigravity.json")


def uso_antigravity(validade=600):
    """Cotas do Antigravity pelo comando oficial `agy -p /usage` (o mesmo que o Maestri usa).

    O comando é uma consulta local de cota, sem chamada ao modelo; ainda assim fica em cache por 10 min.
    Devolve só o grupo "Gemini Models" (o que os recrutas Gemini consomem).
    """
    try:
        with open(CACHE_AGY, encoding="utf-8") as f:
            c = json.load(f)
        if time.time() - c.get("_lido", 0) < validade:
            return c["dados"]
    except (OSError, ValueError, KeyError):
        pass
    if not os.path.exists(AGY):
        return {"fonte": "indisponivel"}
    try:
        env = dict(os.environ, MSYS_NO_PATHCONV="1")
        out = subprocess.run([AGY, "-p", "/usage", "--output-format", "json"], capture_output=True,
                             text=True, encoding="utf-8", errors="ignore", timeout=90, cwd=CASA, env=env).stdout
        d = json.loads(out)
        grupos = d["command"]["data"]["groups"]
    except Exception:
        return {"fonte": "indisponivel"}
    g = next((g for g in grupos if "gemini" in g.get("name", "").lower()), grupos[0] if grupos else None)
    if not g:
        return {"fonte": "indisponivel"}
    jan = {b.get("window"): b for b in g.get("buckets", [])}
    pct = lambda b: round(100 * (1 - float(b.get("remaining_fraction", 1))), 1) if b else None
    dados = {
        "fonte": "exato",
        "janela5h_pct": pct(jan.get("5h")),
        "janela5h_reset": iso((jan.get("5h") or {}).get("reset_time")),
        "semana_pct": pct(jan.get("weekly")),
        "semana_reset": iso((jan.get("weekly") or {}).get("reset_time")),
    }
    try:
        with open(CACHE_AGY, "w", encoding="utf-8") as f:
            json.dump({"_lido": time.time(), "dados": dados}, f)
    except OSError:
        pass
    return dados


# ---------------- Claude ----------------

def eventos_claude(desde):
    """(timestamp, peso) de cada resposta e lista de rejeições de 5 h, em todos os projetos."""
    eventos, rejeicoes = [], []
    limite_mtime = (desde - timedelta(hours=1)).timestamp()
    for arq in glob.glob(os.path.join(CASA, ".claude", "projects", "*", "*.jsonl")):
        if os.path.getmtime(arq) < limite_mtime:
            continue
        for reg in ler_jsonl(arq):
            ts = reg.get("timestamp")
            if not ts:
                continue
            try:
                t = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except ValueError:
                continue
            if t < desde:
                continue
            q = reg.get("quotaLimits")
            if isinstance(q, dict) and q.get("status") == "rejected" and q.get("rateLimitType") == "five_hour":
                rejeicoes.append(t)
            u = (reg.get("message") or {}).get("usage") if isinstance(reg.get("message"), dict) else None
            if isinstance(u, dict):
                peso = sum(float(u.get(k) or 0) * w for k, w in PESOS.items())
                if peso:
                    eventos.append((t, peso))
    eventos.sort()
    return eventos, sorted(rejeicoes)


def blocos(eventos):
    """Agrupa em blocos de 5 h a partir da primeira mensagem (como o limite do Claude)."""
    res = []
    for t, p in eventos:
        if not res or t >= res[-1]["inicio"] + JANELA:
            res.append({"inicio": t, "total": 0.0})
        res[-1]["total"] += p
    return res


def uso_claude_exato():
    """Mesma fonte do /usage do Claude Code: API de uso da Anthropic com o login OAuth local.
    O token só vai para api.anthropic.com. Devolve None se não houver login ou a API falhar."""
    try:
        cred = json.load(open(os.path.join(CASA, ".claude", ".credentials.json"), encoding="utf-8"))
        tok = cred["claudeAiOauth"]["accessToken"]
        req = urllib.request.Request("https://api.anthropic.com/api/oauth/usage", headers={
            "Authorization": "Bearer " + tok, "anthropic-beta": "oauth-2025-04-20", "User-Agent": "claude-code"})
        d = json.load(urllib.request.urlopen(req, timeout=15))
        h, s = d["five_hour"], d["seven_day"]
        dados = {
            "fonte": "exato",
            "janela5h_pct": round(float(h["utilization"]), 1),
            "janela5h_reset": iso(h.get("resets_at")),
            "semana_pct": round(float(s["utilization"]), 1),
            "semana_reset": iso(s.get("resets_at")),
        }
        with open(CACHE_CLAUDE, "w", encoding="utf-8") as f:
            json.dump({"_lido": time.time(), "dados": dados}, f)
        return dados
    except Exception:
        # API fora do ar ou limitando: usa a última leitura exata de até 15 min.
        try:
            with open(CACHE_CLAUDE, encoding="utf-8") as f:
                c = json.load(f)
            if time.time() - c.get("_lido", 0) < 900:
                return c["dados"]
        except (OSError, ValueError, KeyError):
            pass
        return None


def uso_claude():
    exato = uso_claude_exato()
    if exato:
        return exato
    eventos, rejeicoes = eventos_claude(agora() - timedelta(days=8))
    bl = blocos(eventos)
    atual = bl[-1] if bl and agora() < bl[-1]["inicio"] + JANELA else None
    teto = None
    if rejeicoes:
        r = rejeicoes[-1]
        for b in bl:
            if b["inicio"] <= r < b["inicio"] + JANELA:
                teto = sum(p for t, p in eventos if b["inicio"] <= t <= r)
                break
    usado = atual["total"] if atual else 0.0
    return {
        "fonte": "estimado" if teto else "sem_calibracao",
        "janela5h_pct": round(100 * usado / teto, 1) if teto else None,
        "janela5h_consumo": round(usado),
        "janela5h_teto_estimado": round(teto) if teto else None,
        "janela5h_reset": (atual["inicio"] + JANELA).astimezone().strftime("%Y-%m-%d %H:%M") if atual else None,
        "ultima_rejeicao": rejeicoes[-1].astimezone().strftime("%Y-%m-%d %H:%M") if rejeicoes else None,
    }


# ---------------- Resumo e alertas ----------------

def pressao(f):
    """Maior percentual entre a janela de 5 h e a semana (o que acabar primeiro manda)."""
    v = [f.get(k) for k in ("janela5h_pct", "semana_pct") if f.get(k) is not None]
    return max(v) if v else None


def resumo():
    c, x, g = uso_claude(), uso_codex(), uso_antigravity()
    pc, px = pressao(c), pressao(x)
    if pc is None or px is None:
        rec = "codex" if (px is not None and px < 60) else "indefinido"
    else:
        rec = "codex" if px + 10 < pc else ("claude" if pc + 10 < px else "equilibrado")
    familias = {"claude": pc, "codex": px, "gemini": pressao(g)}
    validas = {k: v for k, v in familias.items() if v is not None}
    if validas:
        menor = min(validas, key=validas.get)
        resto = [v for k, v in validas.items() if k != menor]
        rec = menor if resto and min(resto) - validas[menor] >= 10 else "equilibrado"
    return {"gerado_em": agora().astimezone().strftime("%Y-%m-%d %H:%M"), "claude": c, "codex": x, "gemini": g, "preferir": rec}


def alertas(r, limite):
    out = []
    for nome in ("claude", "codex", "gemini"):
        pct = r[nome].get("janela5h_pct")
        if pct is not None and pct >= limite:
            out.append(f"{nome} em {pct}% da janela de 5 h (reset {r[nome].get('janela5h_reset')})")
    for nome in ("claude", "codex", "gemini"):
        sem = r[nome].get("semana_pct")
        if sem is not None and sem >= limite:
            out.append(f"{nome} em {sem}% do limite semanal (reset {r[nome].get('semana_reset')})")
    ps = {k: pressao(r[k]) for k in ("claude", "codex", "gemini") if pressao(r[k]) is not None}
    if len(ps) >= 2 and max(ps.values()) - min(ps.values()) >= 35:
        desc = " x ".join(f"{k} {v}%" for k, v in ps.items())
        out.append(f"uso desequilibrado ({desc}): preferir {r['preferir']}")
    return out


def texto(r):
    c, x = r["claude"], r["codex"]
    if c.get("fonte") == "exato":
        lc = f"Claude 5h: {c['janela5h_pct']}% (reset {c['janela5h_reset']}) | semana: {c['semana_pct']}% (reset {c['semana_reset']})"
    elif c["janela5h_pct"] is not None:
        lc = f"Claude 5h: {c['janela5h_pct']}% (estimado; reset {c['janela5h_reset']})"
    else:
        lc = f"Claude 5h: consumo {c['janela5h_consumo']} (sem calibração)"
    lx = (f"Codex 5h: {x['janela5h_pct']}% (reset {x['janela5h_reset']}) | semana: {x['semana_pct']}% (reset {x['semana_reset']})"
          if x.get("janela5h_pct") is not None else "Codex: indisponível")
    g = r.get("gemini") or {}
    lg = (f"Gemini 5h: {g['janela5h_pct']}% (reset {g['janela5h_reset']}) | semana: {g['semana_pct']}% (reset {g['semana_reset']})"
          if g.get("janela5h_pct") is not None else "Gemini: indisponível")
    return f"[{r['gerado_em']}] {lc} | {lx} | {lg} | preferir: {r['preferir']}"


def avisar(alvo, msg):
    cli = os.environ.get("MAESTRI_CLI") or "maestri"
    try:
        subprocess.run([cli, "ask", alvo, msg], timeout=30, capture_output=True)
    except Exception as e:  # o vigia nunca pode cair por falha de aviso
        print(f"falha ao avisar: {e}", file=sys.stderr)


def alvo_padrao():
    arq = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sentinela-alvo.txt")
    try:
        with open(arq, encoding="utf-8") as f:
            return f.read().strip() or "Claude Code Maestro"
    except OSError:
        return "Claude Code Maestro"


COR = {"ok": "\033[32m", "atencao": "\033[33m", "alto": "\033[31m", "fim": "\033[0m", "neg": "\033[1m", "fraco": "\033[2m"}


def barra(pct, largura=20):
    if pct is None:
        return COR["fraco"] + "·" * largura + COR["fim"] + "   --"
    cheio = min(largura, round(largura * pct / 100))
    cor = COR["ok"] if pct < 50 else COR["atencao"] if pct < 75 else COR["alto"]
    return f"{cor}{'█' * cheio}{COR['fraco']}{'░' * (largura - cheio)}{COR['fim']} {cor}{pct:5.1f}%{COR['fim']}"


def hora(reset):
    return f"{reset[8:10]}/{reset[5:7]} {reset[11:16]}" if reset else "--"


def painel(r, limite, avisos):
    linhas = [f"{COR['neg']}SENTINELA DE USO{COR['fim']}  {r['gerado_em']}   limite de alerta {limite:.0f}%   "
              f"preferir: {COR['neg']}{r['preferir']}{COR['fim']}", ""]
    linhas.append(f"{'':8}{'janela 5 h':<28}{'reinicia':<14}{'semana':<28}{'reinicia'}")
    for nome, rot in (("claude", "Claude"), ("codex", "Codex"), ("gemini", "Gemini")):
        f = r.get(nome) or {}
        linhas.append(f"{rot:<8}{barra(f.get('janela5h_pct'))}  {hora(f.get('janela5h_reset')):<12}"
                      f"{barra(f.get('semana_pct'))}  {hora(f.get('semana_reset'))}")
    linhas.append("")
    linhas.append(f"{COR['fraco']}Últimos alertas:{COR['fim']}" if avisos else f"{COR['fraco']}Sem alertas.{COR['fim']}")
    linhas += [f"  {a}" for a in avisos[-5:]]
    return "\n".join(linhas)


def vigiar(intervalo, limite, alvo):
    alvo = alvo or alvo_padrao()
    print(f"Sentinela: avisando '{alvo}' (limite {limite}%, a cada {intervalo} s)", flush=True)
    ja_avisado = set()
    historico = []
    if os.name == "nt":
        os.system("")  # liga as sequências ANSI no console do Windows
    while True:
        r = resumo()
        atuais = alertas(r, limite)
        # Chave sem o percentual: avisa uma vez por tipo de alerta até a situação normalizar.
        chave = lambda a: " ".join(a.split()[:2]) + (" semanal" if "semanal" in a else "")
        novos = [a for a in atuais if chave(a) not in ja_avisado]
        if novos:
            avisar(alvo, "Sentinela de uso: " + "; ".join(novos) + ". Siga a skill agendar-retomada e a regra de equilibrio de brain/orquestracao.md. Status: " + texto(r))
            ja_avisado |= {chave(a) for a in novos}
            historico += [f"{r['gerado_em'][11:]} {a}" for a in novos]
        print("\033[2J\033[H" + painel(r, limite, historico) + f"\n\n{COR['fraco']}Avisando '{alvo}' a cada {intervalo} s.{COR['fim']}", flush=True)
        # Esquece alertas que voltaram ao normal (ex.: reset da janela).
        ja_avisado &= {chave(a) for a in atuais}
        time.sleep(intervalo)


def sentinela(intervalo, limite):
    """Cria (ou recria) o terminal Sentinela no Maestri, já apontado para o terminal do maestro."""
    import re
    cli = os.environ.get("MAESTRI_CLI") or "maestri"
    try:
        lista = subprocess.run([cli, "list"], capture_output=True, text=True, encoding="utf-8",
                               errors="ignore", timeout=30).stdout
    except Exception as e:
        sys.exit(f"não consegui rodar '{cli} list' (defina MAESTRI_CLI com o caminho do maestri): {e}")
    m = re.search(r'You:\s*\n\s*-\s*name:\s*"([^"]+)"', lista)
    if not m:
        sys.exit("não achei o terminal do maestro (linha após 'You:' em maestri list); precisa estar no Modo Maestro")
    maestro = m.group(1)
    aqui = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(aqui, "sentinela-alvo.txt"), "w", encoding="utf-8") as f:
        f.write(maestro)
    script = os.path.abspath(__file__).replace("\\", "/")
    # Sem aspas internas: o terminal do Sentinela é PowerShell. Nome com espaço fica só no sentinela-alvo.txt.
    cmd = f"python {script} vigiar --intervalo {intervalo} --limite {limite:g}" + ("" if " " in maestro else f" --avisar {maestro}")
    existe = re.search(r'name:\s*"Sentinela"', lista) is not None
    args = [cli, "recruit", "--preset", "Shell", "--command", cmd, "--replace", "Sentinela"] if existe \
        else [cli, "recruit", "Sentinela", "--preset", "Shell", "--command", cmd]
    r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="ignore", timeout=60)
    if r.returncode != 0:
        sys.exit(f"falha ao recrutar o Sentinela: {(r.stderr or r.stdout).strip()}")
    print(f"Sentinela {'recriado' if existe else 'criado'}: avisa '{maestro}' (limite {limite:g}%, a cada {intervalo} s). "
          f"Confira com: maestri check \"Sentinela\"")


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    sub.add_parser("json")
    v = sub.add_parser("vigiar")
    v.add_argument("--intervalo", type=int, default=120)
    v.add_argument("--limite", type=float, default=75)
    v.add_argument("--avisar", default=None)
    s = sub.add_parser("sentinela")
    s.add_argument("--intervalo", type=int, default=120)
    s.add_argument("--limite", type=float, default=75)
    a = p.parse_args()
    if a.cmd == "status":
        print(texto(resumo()))
    elif a.cmd == "json":
        print(json.dumps(resumo(), ensure_ascii=False, indent=2))
    elif a.cmd == "sentinela":
        sentinela(a.intervalo, a.limite)
    else:
        vigiar(a.intervalo, a.limite, a.avisar)


if __name__ == "__main__":
    main()
