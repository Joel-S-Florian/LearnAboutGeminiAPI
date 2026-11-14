# 09.1 Primer agente gestionado (Antigravity): en vez de un modelo, llamas a un AGENTE que corre en un
# sandbox Linux de Google. Un solo llamado crea el sandbox, ejecuta el bucle del agente (planear, ejecutar
# codigo, leer/escribir archivos, observar, repetir) y devuelve el resultado.
# Tres parametros clave: agent=..., environment="remote" (sandbox nuevo) e input (la tarea).
# El agente puede gastar MUCHOS tokens: por eso ponemos un tope con agent_config.max_total_tokens.

from google import genai

# Los agentes gestionados requieren la version v1beta; timeout generoso (5 min, en milisegundos)
client = genai.Client(http_options={"api_version": "v1beta", "timeout": 300_000})

try:
    interaction = client.interactions.create(
        agent="antigravity-preview-09-2026",
        input="Write a Python script that generates the first 20 Fibonacci numbers and saves them to "
        "fibonacci.txt. Then read the file and print its contents.",
        environment="remote",
        # Freno de presupuesto (entrada + salida + razonamiento). Si lo alcanza, status = "incomplete".
        # 80.000 queda por debajo del limite de 100K tokens/minuto que muestra rate_limit/*.json
        agent_config={"type": "antigravity", "max_total_tokens": 80_000},
    )
except Exception as e:
    raise SystemExit(f"fallo: {type(e).__name__} {getattr(e, 'status_code', None)} {str(e)[:300]}")

print(f"Salida:\n{interaction.output_text}")

# Los metadatos van AL FINAL: la salida del agente puede ser larga y asi no se pierden al recortar
print("\n===== METADATOS =====")
print(f"Interaction ID: {interaction.id}")
# environment_id identifica el sandbox: sirve para reusarlo despues (con sus archivos y estado)
print(f"Environment ID: {interaction.environment_id}")
print(f"Estado: {interaction.status}")
usage = getattr(interaction, "usage", None)
if usage:
    print(f"Tokens usados: {usage.total_tokens}")
# El agente hace muchos pasos (codigo, ejecucion, archivos...): contar los tipos que hubo
from collections import Counter

print("Pasos:", dict(Counter(s.type for s in (interaction.steps or []))))
