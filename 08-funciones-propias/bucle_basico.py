# 08.1 Function calling: el modelo llama a TUS funciones (modo "stateful")
# Flujo (el modelo NUNCA ejecuta tu codigo):
#   1. Declaras la funcion: nombre, descripcion y parametros (JSON Schema).
#   2. El modelo decide si hace falta y devuelve un paso "function_call" con los argumentos.
#   3. TU codigo ejecuta la funcion y devuelve un "function_result" con el mismo call_id.
#   4. El modelo usa el resultado y redacta la respuesta final.
# "Stateful": el servidor recuerda la conversacion; solo envias previous_interaction_id.

import json

from google import genai

# Lista de modelos con respaldo (ver BITACORA.md). Solo se prueba en el PRIMER turno;
# despues se sigue con el que respondio, porque la conversacion queda ligada a el.
MODELOS = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-2.5-flash-lite"]

client = genai.Client(http_options={"timeout": 60_000})

# 1. Declaracion de la herramienta: un dict con type "function"
weather_tool = {
    "type": "function",
    "name": "get_current_temperature",
    # La descripcion es lo que el modelo lee para decidir cuando llamarla: que sea clara
    "description": "Gets the current temperature for a given location.",
    "parameters": {
        "type": "object",
        "properties": {
            "location": {"type": "string", "description": "The city name, e.g. San Francisco"},
        },
        "required": ["location"],
    },
}

# Tus funciones reales: nombre -> codigo. Aqui es un dato fijo (no consulta ningun clima)
available_functions = {
    "get_current_temperature": lambda location: {
        "location": location, "temperature": "22", "unit": "celsius"
    },
}

user_input = "What is the temperature in London?"
previous_id = None

while True:
    interaction = None
    for modelo in MODELOS:
        try:
            interaction = client.interactions.create(
                model=modelo,
                input=user_input,
                tools=[weather_tool],
                previous_interaction_id=previous_id,
            )
            MODELOS = [modelo]  # fijar el modelo que funciono
            break
        except Exception as e:
            print(f"[{modelo}] fallo: {type(e).__name__} {getattr(e, 'status_code', None)}")
    if interaction is None:
        raise SystemExit("Ningun modelo respondio.")

    # 2-3. Buscar peticiones de llamada y ejecutarlas localmente
    function_results = []
    for step in interaction.steps:
        if step.type == "function_call":
            result = available_functions[step.name](**step.arguments)
            print(f"Called {step.name}({step.arguments}) -> {result}")
            function_results.append({
                "type": "function_result",
                "name": step.name,
                "call_id": step.id,  # une el resultado con SU llamada
                "result": [{"type": "text", "text": json.dumps(result)}],
            })

    # Si el modelo ya no pidio ninguna funcion, esta es la respuesta final
    if not function_results:
        break

    # 4. El siguiente turno de la conversacion son los resultados
    user_input = function_results
    previous_id = interaction.id

print(interaction.output_text)
