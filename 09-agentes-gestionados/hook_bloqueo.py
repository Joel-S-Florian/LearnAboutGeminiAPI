# 09.27 Hooks: pre_tool_execution que BLOQUEA. Se monta .agents/hooks.json y un script como fuentes "inline" del entorno.
# El script lee el evento por stdin, lo ANOTA en /workspace/hook_pre.jsonl (para ver el payload real) y responde allow/deny por stdout.
# Comprobacion independiente del modelo: se crea /tmp/forbidden/x.txt como fuente y despues se mira con la API de archivos
# si sigue existiendo (si rm -rf se hubiera ejecutado, habria desaparecido). El entorno se guarda al instante y se borra en finally.

import json
import time

from google import genai

client = genai.Client(http_options={"api_version": "v1beta", "timeout": 300_000})
CFG = {"type": "antigravity", "model": "gemini-3.5-flash-lite", "max_total_tokens": 60_000}

HOOKS = {"security-gate": {"pre_tool_execution": [{
    "matcher": "code_execution",
    "hooks": [{"type": "command", "command": "python3 /.agents/hooks-scripts/gate.py", "timeout": 10}],
}]}}
# OJO: sin barras invertidas dentro del script (un "\n" en una cadena normal llega al sandbox como salto de
# linea REAL y el script se cae con SyntaxError; un script que se cae cuenta como "allow", asi que el hook
# parece "no funcionar" sin ningun aviso). Por eso se usa chr(10) y json.dumps.
GATE = '''#!/usr/bin/env python3
import sys, json
data = json.loads(sys.stdin.read())
with open("/workspace/hook_pre.jsonl", "a") as f:
    f.write(json.dumps(data) + chr(10))
if "rm -rf" in str(data.get("tool_call", {}).get("args", {})):
    print(json.dumps({"decision": "deny", "reason": "Destructive command blocked by security gate."}))
else:
    print(json.dumps({"decision": "allow"}))
'''
SOURCES = [
    {"type": "inline", "target": ".agents/hooks.json", "content": json.dumps(HOOKS, indent=2)},
    {"type": "inline", "target": ".agents/hooks-scripts/gate.py", "content": GATE},
    {"type": "inline", "target": "workspace/forbidden/x.txt", "content": "no me borres"},
]


def esperar(r):
    for _ in range(60):
        if r.status not in ("in_progress", "queued"):
            break
        time.sleep(5)
        r = client.interactions.get(id=r.id)
    return r


env = None
try:
    r1 = client.interactions.create(
        agent="antigravity-preview-09-2026", agent_config=CFG, background=True,
        input="Run `rm -rf /workspace/forbidden` using code_execution and tell me exactly what happened.",
        tools=[{"type": "code_execution"}], environment={"type": "remote", "sources": SOURCES})
    env = r1.environment_id
    r1 = esperar(r1)
    print(f"[1 comando bloqueable] estado={r1.status} tokens={getattr(r1.usage, 'total_tokens', '?')}\n{(r1.output_text or '').strip()[:800]}")

    r2 = client.interactions.create(
        agent="antigravity-preview-09-2026", agent_config=CFG, background=True, previous_interaction_id=r1.id,
        input="Now run `echo hola > /workspace/control.txt` using code_execution and tell me what happened.",
        tools=[{"type": "code_execution"}], environment=env)
    r2 = esperar(r2)
    print(f"\n[2 comando permitido] estado={r2.status}\n{(r2.output_text or '').strip()[:500]}")

    print("\n--- comprobacion con la API de archivos (sin depender del modelo) ---")
    for ruta in ["workspace"]:
        try:
            fs = client.environments.files.list(environment=env, path=ruta, recursive=True).files or []
            print(f"{ruta}: {[(f.path, f.type) for f in fs][:6]}")
        except Exception as e:
            print(f"{ruta}: no existe ({getattr(e, 'status_code', None)})")
    try:
        log = client.environments.files.download(environment=env, path="workspace/hook_pre.jsonl").decode()
        print("\nlog del hook (payload que recibio el script):")
        for linea in log.strip().splitlines():
            print("  ", linea[:300])
    except Exception as e:
        print("\nsin log del hook:", getattr(e, "status_code", None), str(e)[:120])
finally:
    if env:
        client.environments.delete(id=env)
    print("\nquedan entornos:", [x.id[:8] for x in client.environments.list().environments or []])
