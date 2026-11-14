# 08.5 Function calling "stateless": TU guardas el historial, el servidor no recuerda nada.
# Con store=False no hay previous_interaction_id: en cada peticion mandas TODO el historial en input:
#   1. el user_input inicial
#   2. todos los pasos que devolvio el modelo, EXACTAMENTE como llegaron (incluye "thought")
#   3. el function_result con lo que devolvio tu funcion

import json

from google import genai

MODELOS = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-2.5-flash-lite"]

client = genai.Client(http_options={"timeout": 60_000})

set_light_values_declaration = {
    "type": "function",
    "name": "set_light_values",
    "description": "Sets the brightness and color temperature of a light.",
    "parameters": {
        "type": "object",
        "properties": {
            "brightness": {"type": "integer", "description": "Light level from 0 to 100"},
            "color_temp": {"type": "string", "enum": ["daylight", "cool", "warm"]},
        },
        "required": ["brightness", "color_temp"],
    },
}


def set_light_values(brightness: int, color_temp: str) -> dict:
    return {"brightness": brightness, "colorTemperature": color_temp}


# El historial vive en tu variable. Cada elemento es un "paso" (step)
history = [
    {
        "type": "user_input",
        "content": [{"type": "text", "text": "Turn the lights down to a romantic level"}],
    }
]

interaction = None
modelo_usado = None
for modelo in MODELOS:
    try:
        interaction = client.interactions.create(
            model=modelo,
            store=False,  # el servidor NO guarda la conversacion
            input=history,
            tools=[set_light_values_declaration],
        )
        modelo_usado = modelo
        print(f"Modelo usado: {modelo}")
        break
    except Exception as e:
        print(f"[{modelo}] fallo: {type(e).__name__} {getattr(e, 'status_code', None)}")
if interaction is None:
    raise SystemExit("Ningun modelo respondio.")

# Guardar los pasos del modelo tal cual (model_dump convierte cada paso a dict)
for step in interaction.steps:
    history.append(step.model_dump())
print("Pasos guardados en el historial:", [h["type"] for h in history])

# Ejecutar tu función
# 1. next(...) toma el primer paso de tipo function_call.
# 2. **fc_step.arguments convierte {'brightness': 20, 'color_temp': 'warm'} en argumentos con nombre.
fc_step = next(s for s in interaction.steps if s.type == "function_call")
result = set_light_values(**fc_step.arguments)
print("Resultado de mi funcion:", result)

# Añadir el resultado
# call_id une el resultado con esa llamada. Si no coincide, el modelo no sabe a qué pregunta responde.
history.append(
    {
        "type": "function_result",
        "name": fc_step.name,
        "call_id": fc_step.id,
        "result": [{"type": "text", "text": json.dumps(result)}],
    }
)

# Segunda peticion: el historial completo reemplaza a previous_interaction_id
final_interaction = client.interactions.create(
    model=modelo_usado,
    store=False,
    input=history,
    tools=[set_light_values_declaration],
)
print("\nRespuesta final:", final_interaction.output_text)
