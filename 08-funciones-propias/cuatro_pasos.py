# 08.4 Los cuatro pasos de function calling, uno por uno (sin bucle), con una luz inteligente.
#   1. Declarar la funcion  2. Llamar al modelo  3. Ejecutar TU funcion  4. Devolver el resultado
# Novedad: "enum" en el esquema limita los valores que el modelo puede elegir.

import json

from google import genai

MODELOS = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-2.5-flash-lite"]

client = genai.Client(http_options={"timeout": 60_000})

# --- Paso 1: declaracion (lo que ve el modelo) ---
set_light_values_declaration = {
    "type": "function",
    "name": "set_light_values",
    "description": "Sets the brightness and color temperature of a light.",
    "parameters": {
        "type": "object",
        "properties": {
            "brightness": {"type": "integer", "description": "Light level from 0 to 100"},
            # enum: el modelo solo puede elegir uno de estos tres textos
            "color_temp": {
                "type": "string",
                "enum": ["daylight", "cool", "warm"],
                "description": "Color temperature",
            },
        },
        "required": ["brightness", "color_temp"],
    },
}


# La funcion real (lo que ejecuta tu codigo). El modelo nunca ve este cuerpo
def set_light_values(brightness: int, color_temp: str) -> dict:
    """Set the brightness and color temperature of a room light."""
    return {"brightness": brightness, "colorTemperature": color_temp}


# --- Paso 2: llamar al modelo con la declaracion ---
interaction = None
modelo_usado = None
for modelo in MODELOS:
    try:
        interaction = client.interactions.create(
            model=modelo,
            input="Turn the lights down to a romantic level",
            tools=[set_light_values_declaration],
        )
        modelo_usado = modelo
        print(f"Modelo usado: {modelo}")
        break
    except Exception as e:
        print(f"[{modelo}] fallo: {type(e).__name__} {getattr(e, 'status_code', None)}")
if interaction is None:
    raise SystemExit("Ningun modelo respondio.")

# --- Paso 3: ejecutar la funcion con los argumentos que eligio el modelo ---
fc_step = next(s for s in interaction.steps if s.type == "function_call")
print("El modelo pide:", fc_step.name, fc_step.arguments)
result = set_light_values(**fc_step.arguments)
print("Resultado de mi funcion:", result)

# --- Paso 4: devolver el resultado al modelo para la respuesta final ---
final_interaction = client.interactions.create(
    model=modelo_usado,  # el MISMO modelo: la conversacion esta ligada a el
    input=[
        {
            "type": "function_result",
            "name": fc_step.name,
            "call_id": fc_step.id,
            "result": [{"type": "text", "text": json.dumps(result)}],
        }
    ],
    tools=[set_light_values_declaration],  # hay que volver a declarar las herramientas
    previous_interaction_id=interaction.id,
)
print("\nRespuesta final:", final_interaction.output_text)
