# 09.2 Multi-turno con agentes: la API guarda DOS estados independientes
#   - Contexto de la conversacion (historial, razonamiento, herramientas)  -> previous_interaction_id
#   - Estado del entorno (archivos, paquetes instalados)                    -> environment (un environment_id)
# Se pasan por separado, asi que se pueden combinar:
#   turno 2: las DOS cosas (el agente recuerda la charla Y ve los archivos)
#   turno 3: SOLO el entorno (conversacion nueva, mismos archivos)
# Cada turno gasta tokens: ponemos tope en cada uno.

from google import genai

client = genai.Client(http_options={"api_version": "v1beta", "timeout": 300_000})
AGENTE = "antigravity-preview-09-2026"
CONFIG = {"type": "antigravity", "max_total_tokens": 80_000}


def turno(titulo, **kwargs):
    try:
        r = client.interactions.create(agent=AGENTE, agent_config=CONFIG, **kwargs)
    except Exception as e:
        raise SystemExit(f"[{titulo}] fallo: {type(e).__name__} {getattr(e, 'status_code', None)} {str(e)[:300]}")
    tokens = r.usage.total_tokens if getattr(r, "usage", None) else "?"
    print(f"\n===== {titulo} =====")
    print((r.output_text or "")[:700])
    print(f"-- estado={r.status} tokens={tokens} entorno={r.environment_id}")
    return r


# Turno 1: sandbox nuevo, crea fibonacci.txt
t1 = turno(
    "Turno 1 (entorno nuevo)",
    input="Write the first 20 Fibonacci numbers to fibonacci.txt, one per line. Reply with just 'done'.",
    environment="remote",
)

# Turno 2: conversacion Y entorno. "Now plot..." solo tiene sentido si recuerda el turno 1,
# y necesita fibonacci.txt, que solo existe en ese entorno
t2 = turno(
    "Turno 2 (misma conversacion + mismo entorno)",
    previous_interaction_id=t1.id,
    environment=t1.environment_id,
    input="Now plot the Fibonacci sequence as a line chart and save it as chart.png. Reply briefly.",
)

# Turno 3: SOLO el entorno (sin previous_interaction_id): conversacion en blanco, archivos intactos
t3 = turno(
    "Turno 3 (solo el entorno: conversacion en blanco)",
    environment=t1.environment_id,
    input="List the files in your working directory. Then say what the last task you were asked to do was, "
    "if you remember one. Reply briefly.",
)
