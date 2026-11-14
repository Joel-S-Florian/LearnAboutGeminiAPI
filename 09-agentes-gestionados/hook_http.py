# 09.31 Hooks HTTP ({"type": "http", "url": ..., "timeout": ...}). Solo se usa httpbin.org (decision de Joel: no se envia nada a
# servicios que guarden datos; el POST lleva solo datos falsos). Como NO se puede leer lo que httpbin recibe ni hacerle devolver un
# "deny", la prueba es INDIRECTA: se mide cuanto tarda el agente entre un hook de comando previo (que anota la hora) y uno posterior.
# El hook pre es una lista ordenada: [comando que anota la hora, hook HTTP]; los handlers corren en orden y el agente ESPERA.
#   H0 sin hook HTTP (linea base)     H1 /delay/2  (responde a los 2 s)      H2 /delay/10 con timeout 3
#   H3 /delay/2 pero httpbin NO esta en la allowlist     H4 http://localhost:8080 (loopback, bloqueado segun la doc)
# Que dispara = el hueco pre->post crece. Que se permite = el archivo del comando existe. El entorno se borra en finally.
# Sin barras invertidas dentro del script del hook (trampa de E3.1).

import json
import time

from google import genai

client = genai.Client(http_options={"api_version": "v1beta", "timeout": 300_000})
CFG = {"type": "antigravity", "model": "gemini-3.5-flash-lite", "max_total_tokens": 40_000}

STAMP = '''#!/usr/bin/env python3
import sys, json, time
sys.stdin.read()
with open("/workspace/t.jsonl", "a") as f:
    f.write(json.dumps({"evento": sys.argv[1], "t": time.time()}) + chr(10))
print(json.dumps({"decision": "allow"}))
'''
PRE = "python3 /.agents/hooks-scripts/stamp.py pre"
POST = "python3 /.agents/hooks-scripts/stamp.py post"


def config(http_url, timeout):
    pre = [{"type": "command", "command": PRE, "timeout": 5}]
    if http_url:
        pre.append({"type": "http", "url": http_url, "timeout": timeout, "headers": {"X-Event-Source": "agent-sandbox"}})
    return {"h": {"pre_tool_execution": [{"matcher": "execute_code", "hooks": pre}],
                  "post_tool_execution": [{"matcher": "execute_code", "hooks": [{"type": "command", "command": POST, "timeout": 5}]}]}}


CASOS = [
    ("H0 sin hook HTTP (linea base)", None, 5, ["httpbin.org"]),
    ("H1 https://httpbin.org/delay/2", "https://httpbin.org/delay/2", 10, ["httpbin.org"]),
    ("H2 https://httpbin.org/delay/10, timeout 3 s", "https://httpbin.org/delay/10", 3, ["httpbin.org"]),
    ("H3 /delay/2 con httpbin FUERA de la allowlist", "https://httpbin.org/delay/2", 10, ["example.com"]),
    ("H4 http://localhost:8080/ (loopback)", "http://localhost:8080/hook", 10, ["httpbin.org"]),
]


def correr(titulo, url, timeout, permitidos):
    hooks = config(url, timeout)
    fuentes = [{"type": "inline", "target": ".agents/hooks.json", "content": json.dumps(hooks, indent=2)},
               {"type": "inline", "target": ".agents/hooks-scripts/stamp.py", "content": STAMP}]
    env = None
    try:
        r = client.interactions.create(
            agent="antigravity-preview-09-2026", agent_config=CFG, background=True, tools=[{"type": "code_execution"}],
            input="Run `echo hecho > /workspace/c.txt` using code execution, exactly once. Do not retry. Reply with one short line.",
            environment={"type": "remote", "sources": fuentes, "network": {"allowlist": [{"domain": d} for d in permitidos]}})
        env = r.environment_id
        for _ in range(100):
            if r.status not in ("in_progress", "queued"):
                break
            time.sleep(5)
            r = client.interactions.get(id=r.id)
        try:
            regs = [json.loads(x) for x in client.environments.files.download(environment=env, path="workspace/t.jsonl").decode().strip().splitlines()]
        except Exception:
            regs = []
        pre = next((x["t"] for x in regs if x["evento"] == "pre"), None)
        post = next((x["t"] for x in regs if x["evento"] == "post"), None)
        fs = [f.path for f in client.environments.files.list(environment=env, path="workspace").files or []]
        gap = f"{post - pre:.1f} s" if pre and post else "-"
        print(f"{titulo:48} | estado={r.status:9} | comando ejecutado: {'si' if 'workspace/c.txt' in fs else 'NO'} | hueco pre->post: {gap} | "
              f"tokens={getattr(r.usage, 'total_tokens', '?')}")
    finally:
        if env:
            client.environments.delete(id=env)


for caso in CASOS:
    correr(*caso)
    time.sleep(10)
print("\nquedan entornos:", [x.id[:8] for x in client.environments.list().environments or []])
