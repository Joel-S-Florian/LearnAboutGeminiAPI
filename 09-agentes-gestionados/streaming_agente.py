# 09.3 Streaming de un agente: con stream=True ves el trabajo del agente EN VIVO (cada paso que da)
# en vez de esperar al final. Util en tareas largas. La doc usa "leer Hacker News y hacer un PDF":
# es caro y depende de la web, asi que usamos una tarea corta con codigo.
# Igual que en el streaming de function calling: miramos QUE tipos de evento llegan antes de filtrar.

from collections import Counter

from google import genai

client = genai.Client(http_options={"api_version": "v1beta", "timeout": 300_000})

try:
    stream = client.interactions.create(
        agent="antigravity-preview-09-2026",
        input="Use Python to compute the sum of the squares of the numbers 1 to 10, and tell me the result.",
        environment="remote",
        agent_config={"type": "antigravity", "max_total_tokens": 60_000},
        stream=True,
    )
except Exception as e:
    raise SystemExit(f"fallo: {type(e).__name__} {getattr(e, 'status_code', None)} {str(e)[:300]}")

vistos = Counter()
linea = 0
for event in stream:
    clave = event.event_type
    paso = getattr(getattr(event, "step", None), "type", None)  # tipo de paso (en step.start)
    delta = getattr(getattr(event, "delta", None), "type", None)  # tipo de trozo (en step.delta)
    etiqueta = clave + (f" [{paso}]" if paso else "") + (f" <{delta}>" if delta else "")
    vistos[etiqueta] += 1
    linea += 1
    print(f"{linea:>3}. {etiqueta}")
    if delta == "text":
        print("     texto:", event.delta.text.replace("\n", " ")[:120])
    if clave == "step.stop" and getattr(event, "usage", None):
        print("     usage:", event.usage)

print("\n===== RESUMEN DE EVENTOS =====")
for k, v in vistos.items():
    print(f"{v:>3} x {k}")
