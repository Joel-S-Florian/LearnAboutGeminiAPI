# 08.17 Notas y limites: con tool_choice "any" (o esquemas complejos) la API "compila" tus declaraciones en una
# maquina de estados que limita la generacion. Si son demasiado complejas (muchos estados, ramas o
# anidamiento), rechaza la peticion con 400 INVALID_ARGUMENT. La doc recomienda: separar herramientas,
# aplanar objetos, recortar enums/anyOf, usar nombres cortos y quitar minItems/maxItems.
# Este script SUBE la complejidad por niveles para ver donde (si es que llega) aparece el 400.
# Los umbrales exactos no los da la doc: lo que salga aqui es de ESTE modelo y ESTA fecha.

from google import genai

MODELO = "gemini-3.5-flash-lite"

client = genai.Client(http_options={"timeout": 60_000})


def propiedad(profundidad, valores_enum):
    """Una propiedad enum; si profundidad > 0, la envuelve en objetos anidados."""
    hoja = {"type": "string", "enum": [f"valor_{i}" for i in range(valores_enum)]}
    if profundidad == 0:
        return hoja
    return {"type": "object", "properties": {"anidado": propiedad(profundidad - 1, valores_enum)}, "required": ["anidado"]}


def herramientas(n_tools, n_props, valores_enum, profundidad):
    tools = []
    for t in range(n_tools):
        props = {f"propiedad_con_nombre_largo_{p}": propiedad(profundidad, valores_enum) for p in range(n_props)}
        tools.append({
            "type": "function",
            "name": f"herramienta_{t}",
            "description": "Does something.",
            "parameters": {"type": "object", "properties": props, "required": list(props)},
        })
    return tools


# (herramientas, propiedades, valores del enum, profundidad de anidamiento)
NIVELES = [
    ("simple", (1, 2, 3, 0)),
    ("medio", (5, 5, 20, 1)),
    ("grande", (20, 8, 50, 2)),
    ("enorme", (60, 10, 100, 4)),
]

import sys

solo = sys.argv[1:]  # opcional: python esquemas_complejos.py enorme  (probar solo ese nivel)
for nombre, params in NIVELES:
    if solo and nombre not in solo:
        continue
    tools = herramientas(*params)
    try:
        r = client.interactions.create(
            model=MODELO,
            input="Call any tool you like.",
            tools=tools,
            generation_config={"tool_choice": "any"},  # el modo que, segun la doc, compila la maquina de estados
        )
        llamadas = [s.name for s in (r.steps or []) if s.type == "function_call"]
        print(f"[{nombre}] {params} -> ACEPTADO, llamo a: {llamadas}")
    except Exception as e:
        print(f"[{nombre}] {params} -> {type(e).__name__} {getattr(e, 'status_code', None)}: {str(e)[:220]}")
