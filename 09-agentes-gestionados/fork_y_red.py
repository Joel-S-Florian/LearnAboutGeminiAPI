# 09.15, 09.16 y 09.18 (red): agente guardado por FORK de un entorno y reglas de RED.
#   FORK: preparas un entorno a mano con el agente base y lo conviertes en agente guardado pasando su
#         environment_id como base_environment: cada invocacion parte de una copia de ese entorno.
#   RED:  "network": {"allowlist": [{"domain": ...}]} limita a donde puede salir el sandbox.
#         Al INVOCAR se puede sobrescribir: las reglas nuevas REEMPLAZAN a las guardadas (las fuentes se conservan).
# Sin credenciales: solo dominios publicos (pypi.org y example.com) y un curl que imprime el codigo HTTP.
# Los agentes guardados son recursos persistentes: se borran al final.

import time

from google import genai

client = genai.Client(http_options={"api_version": "v1beta", "timeout": 300_000})
BASE = "antigravity-preview-09-2026"
CONFIG = {"type": "antigravity", "model": "gemini-3.5-flash-lite", "max_total_tokens": 30_000}
CURL = (
    "Run these two shell commands and report the two HTTP codes, labelled by site (000 means it could not connect):\n"
    "curl -s -o /dev/null -w '%{http_code}' --max-time 15 https://pypi.org\n"
    "curl -s -o /dev/null -w '%{http_code}' --max-time 15 https://example.com\n"
    "Answer in one line."
)
creados = []


def resumen(titulo, r):
    tokens = r.usage.total_tokens if getattr(r, "usage", None) else "?"
    print(f"\n===== {titulo} =====")
    print((r.output_text or "(sin texto)").strip()[:300])
    print(f"-- estado={r.status} tokens={tokens}")


try:
    # --- Fork (10.15) ---
    prep = client.interactions.create(
        agent=BASE, environment="remote", agent_config=CONFIG,
        input="Create the file /workspace/template.txt containing exactly TEMPLATE-OK. Reply with 'done'.",
    )
    resumen("Preparar el entorno a forkear", prep)
    client.agents.create(
        id="estudio-fork", base_agent=BASE, agent_config={"type": "antigravity", "model": "gemini-3.5-flash-lite"},
        system_instruction="Be brief.", base_environment=prep.environment_id,
    )
    creados.append("estudio-fork")
    time.sleep(20)
    r = client.interactions.create(
        agent="estudio-fork", environment="remote",
        input="Print the exact contents of /workspace/template.txt. Reply with the content only.",
    )
    resumen("Invocar el agente forkeado (esperado: TEMPLATE-OK)", r)
    time.sleep(20)

    # --- Referencia: red por defecto (abierta) ---
    r = client.interactions.create(agent=BASE, environment="remote", agent_config=CONFIG, input=CURL)
    resumen("Red por defecto (sin reglas)", r)
    time.sleep(20)

    # --- Reglas de red guardadas: solo pypi.org (10.16) ---
    client.agents.create(
        id="estudio-red", base_agent=BASE, agent_config={"type": "antigravity", "model": "gemini-3.5-flash-lite"},
        base_environment={"type": "remote", "network": {"allowlist": [{"domain": "pypi.org"}]}},
    )
    creados.append("estudio-red")
    r = client.interactions.create(agent="estudio-red", environment="remote", input=CURL)
    resumen("Agente con allowlist solo pypi.org", r)
    time.sleep(20)

    # --- Sobrescribir la red al invocar: ahora solo example.com (10.18) ---
    r = client.interactions.create(
        agent="estudio-red", input=CURL,
        environment={"type": "remote", "network": {"allowlist": [{"domain": "example.com"}]}},
    )
    resumen("Sobrescribir al invocar: solo example.com", r)
finally:
    for agente_id in creados:
        try:
            client.agents.delete(id=agente_id)
            print("Borrado:", agente_id)
        except Exception as e:
            print(f"No se pudo borrar {agente_id}: {type(e).__name__} {str(e)[:120]}")
    try:
        print("list tras borrar ->", [a.id for a in client.agents.list().agents or []])
    except Exception as e:
        print(f"list fallo: {type(e).__name__} {str(e)[:120]}")
