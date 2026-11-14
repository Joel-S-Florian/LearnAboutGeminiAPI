# 08.7 Llamadas COMPOSICIONALES: una funcion depende del resultado de otra, asi que van EN SECUENCIA.
# Aqui el modelo debe: 1) pedir el clima de Londres, 2) VER la temperatura, 3) decidir con que
# valor llamar al termostato (20 si hace mas de 20 grados, 18 si no). La decision la toma el modelo
# DESPUES de recibir tu resultado, por eso hacen falta varios turnos (un bucle).

import json

from google import genai

MODELOS = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-2.5-flash-lite"]

# Cambia este numero para ver como cambia la decision del modelo (25 -> 20 grados; 10 -> 18)
TEMPERATURA_LONDRES = 25

client = genai.Client(http_options={"timeout": 60_000})

get_weather_forecast_declaration = {
    "type": "function",
    "name": "get_weather_forecast",
    "description": "Gets the current weather temperature for a given location.",
    "parameters": {
        "type": "object",
        "properties": {"location": {"type": "string", "description": "The location"}},
        "required": ["location"],
    },
}

set_thermostat_temperature_declaration = {
    "type": "function",
    "name": "set_thermostat_temperature",
    "description": "Sets the thermostat to a desired temperature.",
    "parameters": {
        "type": "object",
        "properties": {"temperature": {"type": "integer", "description": "The temperature in Celsius"}},
        "required": ["temperature"],
    },
}
TOOLS = [get_weather_forecast_declaration, set_thermostat_temperature_declaration]

# Tus funciones (simuladas): el clima es un dato fijo y el termostato solo devuelve lo recibido
funciones = {
    "get_weather_forecast": lambda location: {"location": location, "temperature": TEMPERATURA_LONDRES, "unit": "celsius"},
    "set_thermostat_temperature": lambda temperature: {"status": "ok", "temperature": temperature},
}

user_input = "If it's warmer than 20°C in London, set the thermostat to 20°C, otherwise 18°C."
previous_id = None
turno = 0

while True:
    turno += 1
    interaction = None
    for modelo in MODELOS:
        try:
            interaction = client.interactions.create(
                model=modelo, input=user_input, tools=TOOLS, previous_interaction_id=previous_id
            )
            MODELOS = [modelo]  # seguir con el que respondio
            break
        except Exception as e:
            print(f"[{modelo}] fallo: {type(e).__name__} {getattr(e, 'status_code', None)}")
    if interaction is None:
        raise SystemExit("Ningun modelo respondio.")

    resultados = []
    for step in interaction.steps:
        if step.type == "function_call":
            res = funciones[step.name](**step.arguments)
            print(f"Turno {turno}: {step.name}({step.arguments}) -> {res}")
            resultados.append({
                "type": "function_result",
                "name": step.name,
                "call_id": step.id,
                "result": [{"type": "text", "text": json.dumps(res)}],
            })

    if not resultados:  # sin mas llamadas: el modelo ya dio la respuesta final
        break
    user_input = resultados
    previous_id = interaction.id

print(f"\nTurnos totales: {turno}")
print("Respuesta final:", interaction.output_text)
