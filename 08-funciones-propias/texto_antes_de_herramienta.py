# 08.16 Problema: si tu prompt EXIGE que el modelo escriba texto estructurado (XML, YAML, JSON...)
# justo ANTES de llamar a una herramienta, la llamada puede fallar a veces con "Malformed_Function_Call".
# Solucion preferida de la doc: que las "notas de trabajo" vayan dentro de una funcion especial
# update(...) en vez de texto suelto. Entonces el modelo hace DOS llamadas en el mismo turno:
# update() + la funcion real.
# Este script ejecuta cada variante N veces con el MISMO modelo y cuenta que paso. El fallo de la
# doc es "ocasional": puede no aparecer en pocas pruebas.

from collections import Counter

from google import genai

MODELO = "gemini-3.5-flash-lite"
N = 3  # repeticiones por variante

client = genai.Client(http_options={"timeout": 60_000})

get_temperature = {
    "type": "function",
    "name": "get_current_temperature",
    "description": "Gets the current temperature for a given location.",
    "parameters": {
        "type": "object",
        "properties": {"location": {"type": "string", "description": "The city name"}},
        "required": ["location"],
    },
}

# La funcion update() de la doc (aqui con "object"/"string" en minuscula, como en el resto de la guia)
update = {
    "type": "function",
    "name": "update",
    "description": "Update working notes (previous step analysis, plan, next step, external note).",
    "parameters": {
        "type": "object",
        "properties": {
            "previous_step": {"type": "string", "description": "Key findings and outcomes since the previous step."},
            "plan": {"type": "string", "description": "The current status of the plan."},
            "next_step": {"type": "string", "description": "Brief explanation of the immediate next action."},
            "external": {"type": "string", "description": "A short note shown to the user about what you are ABOUT TO DO."},
        },
        "required": ["previous_step", "plan", "next_step", "external"],
    },
}

# Variante A (la que da problemas): exige un bloque <UPDATE> en texto antes de la herramienta
SYSTEM_A = (
    "Before calling a tool, in every response you MUST first output a single <UPDATE> part with the "
    "sub-tags <plan> and <next_step>. Don't skip this part or any of the required sub-tags."
)
# Variante B (preferida): las notas van en una llamada a update()
SYSTEM_B = (
    "Before calling any other tool, in every response you MUST first call `update` with all required "
    "parameters (previous_step, plan, next_step, external)."
)


def probar(nombre, system, tools):
    resumen = Counter()
    for i in range(N):
        try:
            r = client.interactions.create(
                model=MODELO,
                system_instruction=system,
                input="What is the temperature in Paris?",
                tools=tools,
            )
            pasos = r.steps or []  # a veces steps llega vacio/None: no asumir que es una lista
            llamadas = [s.name for s in pasos if s.type == "function_call"]
            texto = r.output_text or ""
            if llamadas:
                resumen["OK: " + " + ".join(llamadas)] += 1
            elif "default_api" in texto or "<" in texto and "/>" in texto:
                # la llamada salio ESCRITA COMO TEXTO en model_output: no hay function_call que ejecutar
                resumen["FALLO: llamada escrita como texto"] += 1
            else:
                resumen[f"otro (estado {r.status}, steps {len(pasos)}): {texto[:60]!r}"] += 1
            if i == 0:
                print(f"  ejemplo de pasos: {[s.type for s in pasos]}")
        except Exception as e:
            resumen[f"ERROR {type(e).__name__} {getattr(e, 'status_code', None)}: {str(e)[:100]}"] += 1
    print(f"[{nombre}] {N} ejecuciones ->", dict(resumen))


probar("A: texto <UPDATE> antes de la herramienta", SYSTEM_A, [get_temperature])
probar("B: funcion update() + herramienta", SYSTEM_B, [update, get_temperature])
