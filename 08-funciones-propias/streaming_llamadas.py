# 08.13 Streaming de llamadas a funciones: con stream=True la respuesta llega en EVENTOS y los
# argumentos de un function_call pueden llegar PARTIDOS en trozos (deltas). Hay que juntarlos
# (agregarlos) y recien al terminar convertirlos a JSON y ejecutar la funcion.
# Eventos que usamos: step.start (empieza un paso), step.delta (un trozo) e interaction.completed.

import json
from collections import Counter

from google import genai

MODELOS = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite"]

client = genai.Client(http_options={"timeout": 60_000})

weather_tool = {
    "type": "function",
    "name": "get_weather",
    "description": "Gets the weather for a given location.",
    "parameters": {
        "type": "object",
        "properties": {"location": {"type": "string", "description": "The city and state"}},
        "required": ["location"],
    },
}

stream = None
for modelo in MODELOS:
    try:
        stream = client.interactions.create(
            model=modelo,
            input="What is the weather in Paris?",
            tools=[weather_tool],
            stream=True,
        )
        print(f"Modelo usado: {modelo}\n")
        break
    except Exception as e:
        print(f"[{modelo}] fallo: {type(e).__name__} {getattr(e, 'status_code', None)}")
if stream is None:
    raise SystemExit("Ningun modelo respondio.")

current_calls = {}  # index del paso -> llamada en construccion
tool_calls = []  # llamadas completas, listas para ejecutar
vistos = Counter()  # para ver QUE eventos llegan (depuracion)

for event in stream:
    vistos[event.event_type + (f":{event.delta.type}" if event.event_type == "step.delta" else "")] += 1

    if event.event_type == "step.start":
        if event.step.type == "function_call":
            current_calls[event.index] = {"id": event.step.id, "name": event.step.name, "arguments": ""}
            # los argumentos pueden venir ya completos en el inicio del paso
            args = getattr(event.step, "arguments", None)
            if args:
                current_calls[event.index]["arguments"] = json.dumps(args) if isinstance(args, dict) else args

    elif event.event_type == "step.delta":
        # La doc (Python) filtra por "arguments", pero en la ejecucion real el tipo llego como
        # "arguments_delta" (la doc de JavaScript si lo dice asi). Con "arguments" los argumentos
        # quedaban VACIOS ({}) sin ningun error: se aceptan los dos nombres.
        if event.delta.type in ("arguments", "arguments_delta"):
            print("  [delta de argumentos]", event.delta.model_dump())  # depuracion: ver sus campos
            if event.index in current_calls:
                # el campo con el trozo tambien varia segun la doc: partial_arguments o arguments
                trozo = getattr(event.delta, "partial_arguments", None) or getattr(event.delta, "arguments", "")
                current_calls[event.index]["arguments"] += trozo
        elif event.delta.type == "text":
            print(event.delta.text, end="", flush=True)

    elif event.event_type == "interaction.completed":
        for index, call in current_calls.items():
            # solo ahora el texto acumulado es un JSON completo
            args = json.loads(call["arguments"]) if call["arguments"] else {}
            tool_calls.append({"type": "function_call", "id": call["id"], "name": call["name"], "arguments": args})

print("Eventos recibidos:", dict(vistos))
print("Llamadas listas para ejecutar:")
print(json.dumps(tool_calls, indent=2))
