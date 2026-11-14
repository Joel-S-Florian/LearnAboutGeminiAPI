# 09.7 Tus funciones dentro de un agente: el agente puede pedir una funcion TUYA (como en la seccion 9).
# Diferencias con el function calling normal:
#   - El agente se DETIENE con status "requires_action" cuando espera tu resultado.
#   - Las herramientas de ARCHIVOS del sandbox tambien aparecen como function_call, pero el entorno las
#     ejecuta solo (tienen su function_result). Las PENDIENTES son las que no tienen resultado.
#   - Solo funciona en modo stateful (previous_interaction_id); no se puede reconstruir el historial a mano.

from google import genai

client = genai.Client(http_options={"api_version": "v1beta", "timeout": 300_000})
AGENTE = "antigravity-preview-09-2026"
CONFIG = {"type": "antigravity", "max_total_tokens": 50_000}

get_weather_tool = {
    "type": "function",
    "name": "get_weather",
    "description": "Gets the current weather for a given location.",
    "parameters": {
        "type": "object",
        "properties": {"location": {"type": "string", "description": "The city and country, e.g. San Francisco, USA"}},
        "required": ["location"],
    },
}
TOOLS = [{"type": "code_execution"}, get_weather_tool]

# Variante de la prueba (el primer intento con tope en AMBOS turnos dio 400 en el turno 2):
#   python funcion_propia_agente.py ambos | solo1 | ninguno   (por defecto: ninguno = exactamente como la doc)
import sys

VARIANTE = sys.argv[1] if len(sys.argv) > 1 else "ninguno"
cfg1 = {"agent_config": CONFIG} if VARIANTE in ("ambos", "solo1") else {}
cfg2 = {"agent_config": CONFIG} if VARIANTE == "ambos" else {}
# Segundo argumento (el 400 persistio con "ninguno", asi que agent_config NO era la causa). Prueba del turno 2:
#   tools2 = volver a declarar tools en el turno 2 | lista = result como lista de bloques de texto
# RESULTADO: con "tools2" funciona (turno 2 completed); sin volver a declarar tools da 400
# "received tool response but no client tool call is pending". Por eso es el valor por defecto.
EXTRA = sys.argv[2] if len(sys.argv) > 2 else "tools2"
if EXTRA == "tools2":
    cfg2["tools"] = TOOLS
print("Variante:", VARIANTE, EXTRA)

# Turno 1
interaction = client.interactions.create(
    agent=AGENTE,
    input="What is the weather in Tokyo?",
    environment="remote",
    tools=TOOLS,
    **cfg1,
)
print("Turno 1: estado =", interaction.status)
print("Turno 1: pasos =", [(s.type, getattr(s, "name", None)) for s in interaction.steps])

if interaction.status != "requires_action":
    raise SystemExit(f"El agente no pidio mi funcion. Salida: {(interaction.output_text or '')[:300]}")

# Llamadas SIN resultado = las que debo ejecutar yo (las de archivos ya traen su function_result)
ejecutadas = {s.call_id for s in interaction.steps if s.type == "function_result"}
pendientes = [s for s in interaction.steps if s.type == "function_call" and s.id not in ejecutadas]
fc = pendientes[0]
print(f"Pendiente para mi: {fc.name}({fc.arguments}) id={fc.id}")

# Mi funcion (simulada)
resultado = {"temperature": 23, "unit": "celsius"}
if EXTRA == "lista":
    import json

    resultado = [{"type": "text", "text": json.dumps(resultado)}]  # formato de la seccion 9

# Turno 2: stateful (previous_interaction_id) y el MISMO entorno. Aqui "result" va como dict,
# como en el ejemplo de la doc (en la seccion 9 iba como lista de bloques de texto)
final = client.interactions.create(
    agent=AGENTE,
    previous_interaction_id=interaction.id,
    environment=interaction.environment_id,
    input=[{"type": "function_result", "name": fc.name, "call_id": fc.id, "result": resultado}],
    **cfg2,
)
print("\nTurno 2: estado =", final.status)
print("Respuesta:", (final.output_text or "").strip()[:400])
tokens = final.usage.total_tokens if getattr(final, "usage", None) else "?"
print("Tokens (turno 2):", tokens)
