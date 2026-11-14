# 08.8 Modos de llamada: generation_config={"tool_choice": ...} controla COMO usa el modelo las funciones
#   auto (por defecto): el modelo decide si llama a una funcion o responde en texto
#   any:                esta OBLIGADO a llamar a una funcion
#   none:               tiene PROHIBIDO llamar funciones
#   validated:          asegura que los argumentos cumplan el esquema
#   allowed_tools:      restringe a cuales funciones puede llamar (y con que modo)
# El script prueba cada modo con dos prompts: uno que NO necesita la funcion y otro que SI.

from google import genai

MODELOS = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-2.5-flash-lite"]

client = genai.Client(http_options={"timeout": 60_000})

weather_tool = {
    "type": "function",
    "name": "get_current_temperature",
    "description": "Gets the current temperature for a given location.",
    "parameters": {
        "type": "object",
        "properties": {"location": {"type": "string", "description": "The city name"}},
        "required": ["location"],
    },
}

PROMPTS = {
    "sin necesidad": "Tell me a very short joke.",
    "con necesidad": "What is the temperature in Boston?",
}

MODOS = {
    "auto": "auto",
    "any": "any",
    "none": "none",
    "validated": "validated",
    # forma con allowed_tools: modo + lista de funciones permitidas
    "allowed_tools(any)": {"allowed_tools": {"mode": "any", "tools": ["get_current_temperature"]}},
}


def llamar(prompt, tool_choice):
    """Prueba los modelos en orden y devuelve un resumen corto del resultado."""
    global MODELOS
    for modelo in MODELOS:
        try:
            r = client.interactions.create(
                model=modelo,
                input=prompt,
                tools=[weather_tool],
                generation_config={"tool_choice": tool_choice},
            )
            MODELOS = [modelo]
            llamadas = [f"{s.name}({s.arguments})" for s in r.steps if s.type == "function_call"]
            if llamadas:
                return "LLAMA: " + "; ".join(llamadas)
            return "TEXTO: " + (r.output_text or "").strip()[:70]
        except Exception as e:
            ultimo = f"{type(e).__name__} {getattr(e, 'status_code', None)} {str(e)[:120]}"
    return f"ERROR: {ultimo}"


for nombre_modo, valor in MODOS.items():
    print(f"\n== modo: {nombre_modo} ==")
    for etiqueta, prompt in PROMPTS.items():
        print(f"  [{etiqueta}] {llamar(prompt, valor)}")
