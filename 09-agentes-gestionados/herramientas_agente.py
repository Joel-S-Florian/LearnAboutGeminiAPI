# 09.5 Herramientas del agente: por defecto tiene code_execution, google_search y url_context, y las
# herramientas de ARCHIVOS se activan solas al pasar "environment". Solo hace falta el parametro tools
# para RESTRINGIR el conjunto o anadir funciones propias / MCP.
# Probamos la misma tarea dos veces para ver la diferencia:
#   A) herramientas por defecto (sin tools)
#   B) solo code_execution (tools=[{"type": "code_execution"}])
# Se comparan los TIPOS DE PASO: si B no usa google_search/url_context, la restriccion funciona.

import time
from collections import Counter

from google import genai

client = genai.Client(http_options={"api_version": "v1beta", "timeout": 300_000})
CONFIG = {"type": "antigravity", "max_total_tokens": 50_000}
TAREA = (
    "Find the latest stable Python release number and the URL of the page where you found it. "
    "Answer in at most two lines."
)


def correr(titulo, **extra):
    try:
        r = client.interactions.create(
            agent="antigravity-preview-09-2026", input=TAREA, environment="remote", agent_config=CONFIG, **extra
        )
    except Exception as e:
        print(f"\n[{titulo}] fallo: {type(e).__name__} {getattr(e, 'status_code', None)} {str(e)[:250]}")
        return
    print(f"\n===== {titulo} =====")
    print((r.output_text or "").strip()[:500])
    tokens = r.usage.total_tokens if getattr(r, "usage", None) else "?"
    print(f"-- estado={r.status} tokens={tokens}")
    print("-- pasos:", dict(Counter(s.type for s in (r.steps or []))))


correr("A: herramientas por defecto")
time.sleep(40)  # tu limite de Antigravity es de 100K tokens/minuto: dejar respirar entre ejecuciones
correr("B: solo code_execution", tools=[{"type": "code_execution"}])
