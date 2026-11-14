# 09.18 Entornos: variables de entorno (environment={"type": "remote", "env": {...}}).
# Un valor puede ser un texto literal o una referencia a una credencial guardada ({"credential": "id"}).
# La doc avisa: un literal queda en CLARO dentro del sandbox, legible por cualquier proceso y por el propio agente.
# Se comprueba con valores FALSOS (nunca secretos reales): el agente imprime las variables, y se mira si
# client.environments.get() las muestra. Tambien se prueba una referencia a una credencial que NO existe.
# Se borra el entorno al final.

import time

from google import genai

client = genai.Client(http_options={"api_version": "v1beta", "timeout": 300_000})
AGENTE = "antigravity-preview-09-2026"
CONFIG = {"type": "antigravity", "max_total_tokens": 60_000}

env_id = None
try:
    # background=True: la primera version (llamada normal) dio timeout de 300 s y se perdio el id del entorno
    # (quedo huerfano). Asi el id llega ya en la respuesta inicial y se sondea el estado.
    r = client.interactions.create(
        agent=AGENTE,
        agent_config=CONFIG,
        background=True,
        input="Run `printenv NODE_ENV LOG_LEVEL CLAVE_FALSA` in the shell and show me the exact output, one line per variable. Be brief.",
        environment={"type": "remote", "env": {"NODE_ENV": "production", "LOG_LEVEL": "debug", "CLAVE_FALSA": "valor-de-prueba-123"}},
    )
    env_id = r.environment_id
    print("entorno desde el inicio:", env_id, "| estado inicial:", r.status)
    for _ in range(60):
        if r.status not in ("in_progress", "queued"):
            break
        time.sleep(5)
        r = client.interactions.get(id=r.id)
    print("estado:", r.status, "| tokens:", getattr(r.usage, "total_tokens", "?"))
    print("--- el agente ve ---\n", (r.output_text or "")[:500])
    e = client.environments.get(id=env_id)
    dump = e.model_dump() if hasattr(e, "model_dump") else str(e)
    print("\n--- environments.get ---\n", dump)
    print("aparece 'valor-de-prueba-123' en get?:", "valor-de-prueba-123" in str(dump))
finally:
    if env_id:
        client.environments.delete(id=env_id)
        print("\nentorno borrado")

# Referencia a una credencial que no existe
try:
    r2 = client.interactions.create(
        agent=AGENTE, input="Say OK.",
        environment={"type": "remote", "env": {"TOKEN": {"credential": "no-existe-123"}}},
    )
    print("\nOJO: credencial inexistente ACEPTADA, estado:", r2.status)
    client.environments.delete(id=r2.environment_id)
except Exception as ex:
    print(f"\ncredencial inexistente rechazada: {getattr(ex, 'status_code', None)} {str(ex)[:250]}")
