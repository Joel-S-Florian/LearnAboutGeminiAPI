# 08.9 Multi-tool: mezclar herramientas INTEGRADAS (code_execution, google_search...) con TUS funciones
# en la misma peticion. Segun la doc, Gemini 3 y 4 lo hacen "de fabrica" en Interactions, y pasar
# previous_interaction_id hace circular el contexto de la herramienta integrada.
# Reparto: lo integrado lo ejecuta Google; tu funcion (function_call) la ejecutas TU.
# Se prueban dos combinaciones; cada una con su lista de modelos y su version de API.

import json

from google import genai

get_weather = {
    "type": "function",
    "name": "get_weather",
    "description": "Gets the weather for a requested city.",
    "parameters": {
        "type": "object",
        "properties": {"city": {"type": "string", "description": "The city and state, e.g. Boston, MA"}},
        "required": ["city"],
    },
}


def ejecutar_caso(titulo, client, modelos, tools, prompt):
    print(f"\n===== {titulo} =====")
    for modelo in modelos:
        try:
            user_input, previous_id, turno = prompt, None, 0
            while True:
                turno += 1
                r = client.interactions.create(
                    model=modelo, input=user_input, tools=tools, previous_interaction_id=previous_id
                )
                print(f"Turno {turno} pasos:", [s.type for s in r.steps])
                resultados = []
                for s in r.steps:
                    if s.type == "function_call":  # solo MIS funciones las ejecuto yo
                        res = {"response": "Very cold. 22 degrees Fahrenheit."}
                        print(f"  mi funcion: {s.name}({s.arguments}) -> {res}")
                        resultados.append({
                            "type": "function_result", "name": s.name, "call_id": s.id,
                            "result": [{"type": "text", "text": json.dumps(res)}],
                        })
                if not resultados:
                    print(f"[{modelo}] Respuesta final:", (r.output_text or "").strip()[:400])
                    return
                user_input, previous_id = resultados, r.id
        except Exception as e:
            print(f"[{modelo}] fallo: {type(e).__name__} {getattr(e, 'status_code', None)} {str(e)[:200]}")
    print("Ningun modelo respondio.")


# Caso 1: code_execution (integrada) + get_weather (mia). Un prompt que pide las dos cosas
ejecutar_caso(
    "code_execution + funcion propia",
    genai.Client(http_options={"timeout": 60_000}),
    ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite"],
    [{"type": "code_execution"}, get_weather],
    "Calculate the sum of the first 20 prime numbers with code, and tell me the weather in Boston.",
)

# Caso 2: el ejemplo de la doc, google_search + funcion. Search exige v1beta; con los modelos 3.x
# la busqueda dio 429 antes (limite 0/0), por eso se prueba primero 2.5 (no listado por la doc)
ejecutar_caso(
    "google_search + funcion propia (ejemplo de la doc)",
    genai.Client(http_options={"api_version": "v1beta", "timeout": 60_000}),
    ["gemini-2.5-flash", "gemini-3.5-flash-lite"],
    [{"type": "google_search"}, get_weather],
    "What is the northernmost city in the United States? What's the weather like there today?",
)
