# 08.6 Llamadas en PARALELO: un solo turno del modelo puede traer VARIOS function_call
# cuando las funciones son independientes entre si (no necesitan el resultado de la otra).
# Regla: por cada function_call debes devolver un function_result con su propio call_id.

import json

from google import genai

MODELOS = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-2.5-flash-lite"]

client = genai.Client(http_options={"timeout": 60_000})

# Tres funciones independientes: encender la bola disco, poner musica, bajar las luces
power_disco_ball = {"type": "function", "name": "power_disco_ball", "description": "Powers the disco ball.",
    "parameters": {"type": "object", "properties": {"power": {"type": "boolean"}}, "required": ["power"]}}
start_music = {"type": "function", "name": "start_music", "description": "Play music.",
    "parameters": {"type": "object", "properties": {"energetic": {"type": "boolean"}, "loud": {"type": "boolean"}}, "required": ["energetic", "loud"]}}
dim_lights = {"type": "function", "name": "dim_lights", "description": "Dim the lights.",
    "parameters": {"type": "object", "properties": {"brightness": {"type": "number"}}, "required": ["brightness"]}}
TOOLS = [power_disco_ball, start_music, dim_lights]

# Tus funciones reales (aqui solo simulan la accion y devuelven un dict)
funciones = {
    "power_disco_ball": lambda power: {"disco_ball": "on" if power else "off"},
    "start_music": lambda energetic, loud: {"music": "playing", "energetic": energetic, "loud": loud},
    "dim_lights": lambda brightness: {"brightness": brightness},
}

interaction = None
modelo_usado = None
for modelo in MODELOS:
    try:
        interaction = client.interactions.create(
            model=modelo,
            input="Turn this place into a party!",
            tools=TOOLS,
            # tool_choice "any": obliga al modelo a llamar alguna funcion (modos: se ven mas adelante)
            generation_config={"tool_choice": "any"},
        )
        modelo_usado = modelo
        print(f"Modelo usado: {modelo}\n")
        break
    except Exception as e:
        print(f"[{modelo}] fallo: {type(e).__name__} {getattr(e, 'status_code', None)}")
if interaction is None:
    raise SystemExit("Ningun modelo respondio.")

# Cuantos function_call llegaron en UN solo turno?
llamadas = [s for s in interaction.steps if s.type == "function_call"]
print(f"Llamadas en un solo turno: {len(llamadas)}")
resultados = []
for step in llamadas:
    args = ", ".join(f"{k}={v}" for k, v in step.arguments.items())
    print(f"  {step.name}({args})")
    res = funciones[step.name](**step.arguments)
    # un function_result POR CADA llamada, con su call_id
    resultados.append({
        "type": "function_result",
        "name": step.name,
        "call_id": step.id,
        "result": [{"type": "text", "text": json.dumps(res)}],
    })

# Todos los resultados viajan juntos en la siguiente peticion
final = client.interactions.create(
    model=modelo_usado,
    input=resultados,
    tools=TOOLS,
    previous_interaction_id=interaction.id,
)
print("\nRespuesta final:", final.output_text)
