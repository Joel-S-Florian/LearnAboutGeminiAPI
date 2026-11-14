# 09.28 Hooks: matchers y post_tool_execution. Varios grupos de hooks a la vez; TODOS usan el mismo script, que anota en
# /workspace/hooks_log.jsonl que grupo disparo, con que evento (pre/post), que herramienta y si el payload trae "error".
# Asi se comparan los matchers sin fiarse de lo que cuente el modelo. Se prueba ademas:
#   - un grupo con "enabled": false (no debe disparar nunca)
#   - un post-hook que responde deny (la doc dice que se IGNORA: el archivo debe seguir existiendo)
#   - el campo "error" del payload post cuando un comando escribe en stderr
# Sin barras invertidas dentro del script del hook (ver la trampa en la BITACORA). El entorno se borra en finally.

import json
import time
from collections import defaultdict

from google import genai

client = genai.Client(http_options={"api_version": "v1beta", "timeout": 300_000})
CFG = {"type": "antigravity", "model": "gemini-3.5-flash-lite", "max_total_tokens": 80_000}

LOGGER = '''#!/usr/bin/env python3
import sys, json
group, event = sys.argv[1], sys.argv[2]
data = json.loads(sys.stdin.read())
tc = data.get("tool_call", {})
rec = {"group": group, "event": event, "tool": tc.get("name"), "has_error": "error" in data,
       "error": str(data.get("error", ""))[:90], "keys": sorted(data.keys()), "args_keys": sorted((tc.get("args") or {}).keys())}
with open("/workspace/hooks_log.jsonl", "a") as f:
    f.write(json.dumps(rec) + chr(10))
print(json.dumps({"decision": "deny", "reason": "post-hook intenta bloquear"}) if len(sys.argv) > 3 else json.dumps({"decision": "allow"}))
'''


def grupo(nombre, evento, matcher, extra=None, enabled=True):
    cmd = f"python3 /.agents/hooks-scripts/log.py {nombre} {'pre' if evento.startswith('pre') else 'post'}" + (f" {extra}" if extra else "")
    g = {evento: [{"matcher": matcher, "hooks": [{"type": "command", "command": cmd, "timeout": 10}]}]}
    if not enabled:
        g["enabled"] = False
    return g


HOOKS = {
    "pre-todo":       grupo("pre-todo", "pre_tool_execution", ".*"),
    "post-todo":      grupo("post-todo", "post_tool_execution", ".*"),
    "glob-ast-file":  grupo("glob-ast-file", "pre_tool_execution", "*_file"),
    "regex-file":     grupo("regex-file", "pre_tool_execution", ".*_file"),
    "alternancia":    grupo("alternancia", "pre_tool_execution", "view_file|write_to_file"),
    "nombre-doc":     grupo("nombre-doc", "pre_tool_execution", "code_execution"),
    "nombre-real":    grupo("nombre-real", "pre_tool_execution", "execute_code"),
    "solo-asterisco": grupo("solo-asterisco", "pre_tool_execution", "*"),
    "cadena-vacia":   grupo("cadena-vacia", "pre_tool_execution", ""),
    "desactivado":    grupo("desactivado", "pre_tool_execution", ".*", enabled=False),
    "post-deny":      grupo("post-deny", "post_tool_execution", "write_to_file", extra="deny"),
}
SOURCES = [
    {"type": "inline", "target": ".agents/hooks.json", "content": json.dumps(HOOKS, indent=2)},
    {"type": "inline", "target": ".agents/hooks-scripts/log.py", "content": LOGGER},
]
PROMPT = ("Do these steps in order, using your FILESYSTEM tools (not the shell) for steps 1-3: "
          "1) create /workspace/a.txt containing 'hola'; 2) read it back; 3) list the /workspace directory; "
          "4) then use code execution to run `ls /carpeta_que_no_existe` (it will fail) and `echo ok`. "
          "Finally reply with one line saying which steps worked.")

env = None
try:
    r = client.interactions.create(agent="antigravity-preview-09-2026", agent_config=CFG, background=True, input=PROMPT,
                                   tools=[{"type": "code_execution"}], environment={"type": "remote", "sources": SOURCES})
    env = r.environment_id
    for _ in range(80):
        if r.status not in ("in_progress", "queued"):
            break
        time.sleep(5)
        r = client.interactions.get(id=r.id)
    print(f"estado={r.status} tokens={getattr(r.usage, 'total_tokens', '?')}\nagente: {(r.output_text or '').strip()[:400]}")

    # el archivo del paso 1 sigue ahi aunque el post-hook respondio deny?
    fs = [f.path for f in client.environments.files.list(environment=env, path="workspace").files or []]
    print("\narchivos en /workspace:", fs)

    log = client.environments.files.download(environment=env, path="workspace/hooks_log.jsonl").decode().strip().splitlines()
    recs = [json.loads(x) for x in log]
    print(f"\n{len(recs)} registros. Herramientas vistas (pre-todo):",
          [x["tool"] for x in recs if x["group"] == "pre-todo"])
    tabla = defaultdict(list)
    for x in recs:
        tabla[x["group"]].append(f"{x['event']}:{x['tool']}")
    print("\ngrupo -> disparos")
    for g in HOOKS:
        print(f"  {g:15} {tabla.get(g, ['(NUNCA disparo)'])}")
    print("\nregistros post con campo error:", [(x["tool"], x["error"]) for x in recs if x["group"] == "post-todo" and x["has_error"]])
    print("claves del payload post:", next((x["keys"] for x in recs if x["group"] == "post-todo"), None))
    print("claves de args por herramienta:", {x["tool"]: x["args_keys"] for x in recs if x["group"] == "pre-todo"})
finally:
    if env:
        client.environments.delete(id=env)
    print("\nquedan entornos:", [x.id[:8] for x in client.environments.list().environments or []])
