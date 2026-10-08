#!/usr/bin/env python3
"""Monitor de limites de uso: Codex (exato, dos logs) e Claude (estimado e calibrado).

Codex grava `rate_limits` (used_percent, resets_at) nos rollouts em ~/.codex/sessions.
Claude só grava tokens por mensagem e o registro `quotaLimits` quando um limite estoura (429);
a estimativa soma o consumo ponderado da janela de 5 h atual e divide pelo consumo que causou
a última rejeição registrada (calibração). Sem rejeição registrada, mostra só o consumo.

Uso:
  uso.py status                     # resumo legível
  uso.py json                       # resumo em JSON
  uso.py vigiar [--intervalo 120] [--limite 75] [--avisar "<terminal do maestro>"]

Sem --avisar, o vigia avisa o terminal escrito em sentinela-alvo.txt (ao lado deste script),
ou "Claude Code Maestro" se o arquivo não existir. Assim o comando do Sentinela não precisa de aspas.
"""
import argparse
import glob
import json
import os
import subprocess
import sys
import time
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
    return datetime.fromtimestamp(float(ts), timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M")


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


def uso_claude():
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

def resumo():
    c, x = uso_claude(), uso_codex()
    pc, px = c.get("janela5h_pct"), x.get("janela5h_pct")
    if pc is None or px is None:
        rec = "codex" if (px is not None and px < 60) else "indefinido"
    else:
        rec = "codex" if px + 10 < pc else ("claude" if pc + 10 < px else "equilibrado")
    return {"gerado_em": agora().astimezone().strftime("%Y-%m-%d %H:%M"), "claude": c, "codex": x, "preferir": rec}


def alertas(r, limite):
    out = []
    for nome in ("claude", "codex"):
        pct = r[nome].get("janela5h_pct")
        if pct is not None and pct >= limite:
            out.append(f"{nome} em {pct}% da janela de 5 h (reset {r[nome].get('janela5h_reset')})")
    sem = r["codex"].get("semana_pct")
    if sem is not None and sem >= limite:
        out.append(f"codex em {sem}% do limite semanal (reset {r['codex'].get('semana_reset')})")
    pc, px = r["claude"].get("janela5h_pct"), r["codex"].get("janela5h_pct")
    if pc is not None and px is not None and abs(pc - px) >= 35:
        out.append(f"uso desequilibrado (claude {pc}% x codex {px}%): preferir {r['preferir']}")
    return out


def texto(r):
    c, x = r["claude"], r["codex"]
    lc = (f"Claude 5h: {c['janela5h_pct']}% (estimado; reset {c['janela5h_reset']})" if c["janela5h_pct"] is not None
          else f"Claude 5h: consumo {c['janela5h_consumo']} (sem calibração)")
    lx = (f"Codex 5h: {x['janela5h_pct']}% (reset {x['janela5h_reset']}) | semana: {x['semana_pct']}% (reset {x['semana_reset']})"
          if x.get("janela5h_pct") is not None else "Codex: indisponível")
    return f"[{r['gerado_em']}] {lc} | {lx} | preferir: {r['preferir']}"


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


def vigiar(intervalo, limite, alvo):
    alvo = alvo or alvo_padrao()
    print(f"Sentinela: avisando '{alvo}' (limite {limite}%, a cada {intervalo} s)", flush=True)
    ja_avisado = set()
    while True:
        r = resumo()
        print(texto(r), flush=True)
        atuais = alertas(r, limite)
        # Chave sem o percentual: avisa uma vez por tipo de alerta até a situação normalizar.
        chave = lambda a: " ".join(a.split()[:2]) + (" semanal" if "semanal" in a else "")
        novos = [a for a in atuais if chave(a) not in ja_avisado]
        if novos:
            avisar(alvo, "Sentinela de uso: " + "; ".join(novos) + ". Siga a skill agendar-retomada e a regra de equilibrio de brain/orquestracao.md. Status: " + texto(r))
            ja_avisado |= {chave(a) for a in novos}
        # Esquece alertas que voltaram ao normal (ex.: reset da janela).
        ja_avisado &= {chave(a) for a in atuais}
        time.sleep(intervalo)


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    sub.add_parser("json")
    v = sub.add_parser("vigiar")
    v.add_argument("--intervalo", type=int, default=120)
    v.add_argument("--limite", type=float, default=75)
    v.add_argument("--avisar", default=None)
    a = p.parse_args()
    if a.cmd == "status":
        print(texto(resumo()))
    elif a.cmd == "json":
        print(json.dumps(resumo(), ensure_ascii=False, indent=2))
    else:
        vigiar(a.intervalo, a.limite, a.avisar)


if __name__ == "__main__":
    main()
