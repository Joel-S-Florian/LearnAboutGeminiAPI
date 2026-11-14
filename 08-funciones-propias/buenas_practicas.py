# 08.15 Buenas practicas de la guia, aplicadas en un solo script:
#   - Descripciones claras y nombres descriptivos        -> en la declaracion
#   - Tipado fuerte (integer, string, enum)              -> parametro "unit" con enum
#   - Validar la llamada ANTES de ejecutar               -> funcion validar()
#   - Manejo de errores robusto                          -> el error vuelve al modelo como function_result
#   - (Seguridad: claves de APIs externas fuera del codigo; aqui no hay APIs reales)
# El prompt pide una ciudad que NO existe en nuestros datos, para ver el manejo de errores.

import json

from google import genai

MODELOS = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite"]

client = genai.Client(http_options={"timeout": 60_000})

get_temperature = {
    "type": "function",
    "name": "get_current_temperature",  # nombre descriptivo, sin espacios ni caracteres raros
    "description": "Gets the current temperature of a city from the local weather table. "
    "Only some cities are available; returns an error if the city is unknown.",
    "parameters": {
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "The city name, e.g. London"},
            "unit": {"type": "string", "enum": ["celsius", "fahrenheit"], "description": "Temperature unit"},
        },
        "required": ["city", "unit"],
    },
}

DATOS = {"london": 9.0, "paris": 11.0, "madrid": 16.0}  # grados Celsius
FUNCIONES_PERMITIDAS = {"get_current_temperature"}  # lista blanca: solo se ejecuta lo que esta aqui


def validar(call):
    """Devuelve un mensaje de error si la llamada no es valida, o None si se puede ejecutar."""
    if call.name not in FUNCIONES_PERMITIDAS:
        return f"unknown function: {call.name}"
    args = call.arguments or {}
    if not isinstance(args.get("city"), str) or not args["city"].strip():
        return "city must be a non-empty string"
    if args.get("unit") not in ("celsius", "fahrenheit"):
        return "unit must be 'celsius' or 'fahrenheit'"
    return None


def ejecutar(args):
    c = DATOS.get(args["city"].strip().lower())
    if c is None:
        return {"error": f"city '{args['city']}' not found", "available": sorted(DATOS)}
    valor = c if args["unit"] == "celsius" else round(c * 9 / 5 + 32, 1)
    return {"city": args["city"], "temperature": valor, "unit": args["unit"]}


def turno(modelos, **kw):
    for m in modelos:
        try:
            return m, client.interactions.create(model=m, **kw)
        except Exception as e:
            print(f"[{m}] fallo: {type(e).__name__} {getattr(e, 'status_code', None)}")
    raise SystemExit("Ningun modelo respondio.")


for prompt in ["What is the temperature in Paris in fahrenheit?", "What is the temperature in Atlantis in celsius?"]:
    print(f"\n### {prompt}")
    modelo, r = turno(MODELOS, input=prompt, tools=[get_temperature])
    resultados = []
    for s in r.steps:
        if s.type != "function_call":
            continue
        error = validar(s)  # 1) validar antes de ejecutar
        res = {"error": error} if error else ejecutar(s.arguments)  # 2) ejecutar o informar el error
        print(f"  {s.name}({s.arguments}) -> {res}")
        resultados.append({
            "type": "function_result", "name": s.name, "call_id": s.id,
            "result": [{"type": "text", "text": json.dumps(res)}],
        })
    if resultados:
        # El error tambien se devuelve al modelo: puede explicarselo al usuario o corregirse
        _, final = turno([modelo], previous_interaction_id=r.id, tools=[get_temperature], input=resultados)
        print("  Respuesta:", final.output_text.strip())
    else:
        print("  (sin llamadas) Respuesta:", r.output_text.strip())
