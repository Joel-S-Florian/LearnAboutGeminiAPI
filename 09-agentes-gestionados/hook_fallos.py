# 09.29 Hooks: que pasa cuando el hook FALLA o responde algo raro. La doc dice: script que se cae, HTTP no-2xx, timeout o JSON
# no reconocido => se trata como "allow" (fail-open). Aqui se comprueba caso por caso. UN script, nueve comportamientos, elegidos
# por una marca en el comando que ejecuta el agente (CASO_1 .. CASO_9). Evidencia independiente del modelo:
#   - /workspace/c<N>.txt: existe si el comando se ejecuto (el agente tiene prohibido reintentar por otra via)
#   - /workspace/hooks_fallos.jsonl: el hook pre y el hook post anotan la hora; post solo aparece si la herramienta corrio
# Sin barras invertidas dentro del script del hook (trampa de E3.1). El script se prueba a mano antes (ver al final del archivo).

import json
import time

from google import genai

client = genai.Client(http_options={"api_version": "v1beta", "timeout": 300_000})
CFG = {"type": "antigravity", "model": "gemini-3.5-flash-lite", "max_total_tokens": 100_000}

SCRIPT = '''#!/usr/bin/env python3
import sys, json, time
evento = sys.argv[1]
data = json.loads(sys.stdin.read())
code = str(data.get("tool_call", {}).get("args", {}).get("code", ""))
caso = next((f"CASO_{n}" for n in range(1, 10) if f"CASO_{n}" in code), None)
if caso:
    with open("/workspace/hooks_fallos.jsonl", "a") as f:
        f.write(json.dumps({"caso": caso, "evento": evento, "t": time.time()}) + chr(10))
if evento == "post" or caso is None:
    print(json.dumps({"decision": "allow"})); sys.exit(0)
DENY = json.dumps({"decision": "deny", "reason": "bloqueado por " + caso})
if caso == "CASO_1": sys.exit(1)                                   # se cae sin imprimir nada
elif caso == "CASO_2": time.sleep(30)                              # se cuelga (el timeout del hook es 3 s)
elif caso == "CASO_3": print("hola mundo")                         # texto plano
elif caso == "CASO_4": print(json.dumps({"foo": "bar"}))           # JSON sin campo decision
elif caso == "CASO_5": print(DENY); sys.exit(1)                    # deny pero con codigo de salida 1
elif caso == "CASO_6": print(json.dumps({"decision": "DENY"}))     # deny en mayusculas
elif caso == "CASO_7": print(json.dumps({"decision": "deny"}))     # deny SIN reason
elif caso == "CASO_8": sys.stderr.write("aviso en stderr"); print(json.dumps({"decision": "allow"}))
elif caso == "CASO_9": print(DENY)                                 # deny normal (referencia)
'''
CASOS = {
    "CASO_1": "se cae (exit 1, sin salida)", "CASO_2": "se cuelga (timeout 3 s)", "CASO_3": "texto plano 'hola mundo'",
    "CASO_4": "JSON sin 'decision'", "CASO_5": "deny + exit 1", "CASO_6": "'DENY' en mayusculas",
    "CASO_7": "deny sin reason", "CASO_8": "allow + stderr", "CASO_9": "deny normal (referencia)",
}
HOOKS = {"fallos": {
    "pre_tool_execution": [{"matcher": "execute_code", "hooks": [
        {"type": "command", "command": "python3 /.agents/hooks-scripts/h.py pre", "timeout": 3}]}],
    "post_tool_execution": [{"matcher": "execute_code", "hooks": [
        {"type": "command", "command": "python3 /.agents/hooks-scripts/h.py post", "timeout": 3}]}],
}}
SOURCES = [
    {"type": "inline", "target": ".agents/hooks.json", "content": json.dumps(HOOKS, indent=2)},
    {"type": "inline", "target": ".agents/hooks-scripts/h.py", "content": SCRIPT},
]
PROMPT = ("Run these 9 shell commands, EACH as its own separate code-execution call (9 calls, in this order). "
          "Do NOT retry any of them, do NOT use any other tool, and continue with the next one even if one fails or is blocked. "
          "At the end, reply with one line per command saying whether it ran or was blocked, and quote any error text.\n"
          + "\n".join(f"{n}. echo {c} > /workspace/c{n}.txt" for n, c in enumerate(CASOS, 1)))

env = None
try:
    t0 = time.time()
    r = client.interactions.create(agent="antigravity-preview-09-2026", agent_config=CFG, background=True, input=PROMPT,
                                   tools=[{"type": "code_execution"}], environment={"type": "remote", "sources": SOURCES})
    env = r.environment_id
    for _ in range(100):
        if r.status not in ("in_progress", "queued"):
            break
        time.sleep(5)
        r = client.interactions.get(id=r.id)
    print(f"estado={r.status} tokens={getattr(r.usage, 'total_tokens', '?')} duracion={time.time() - t0:.0f}s")
    print("agente:\n" + (r.output_text or "").strip()[:1600])

    fs = {f.path for f in client.environments.files.list(environment=env, path="workspace").files or []}
    try:
        regs = [json.loads(x) for x in client.environments.files.download(environment=env, path="workspace/hooks_fallos.jsonl").decode().strip().splitlines()]
    except Exception as e:
        regs = []
        print("SIN LOG del hook:", getattr(e, "status_code", None))
    print("\ncaso                         | pre | post | archivo | pre->post (s)")
    for n, (caso, desc) in enumerate(CASOS.items(), 1):
        pre = next((x["t"] for x in regs if x["caso"] == caso and x["evento"] == "pre"), None)
        post = next((x["t"] for x in regs if x["caso"] == caso and x["evento"] == "post"), None)
        print(f"{n}. {desc:26} | {'si ' if pre else 'NO '} | {'si  ' if post else 'NO  '} | {'existe ' if f'workspace/c{n}.txt' in fs else 'NO     '} | "
              f"{(post - pre):.1f}" if pre and post else f"{n}. {desc:26} | {'si ' if pre else 'NO '} | {'si  ' if post else 'NO  '} | {'existe ' if f'workspace/c{n}.txt' in fs else 'NO     '} | -")
finally:
    if env:
        client.environments.delete(id=env)
    print("\nquedan entornos:", [x.id[:8] for x in client.environments.list().environments or []])
