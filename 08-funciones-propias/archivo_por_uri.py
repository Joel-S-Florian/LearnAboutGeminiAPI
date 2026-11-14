# 08.11 Devolver archivos por URI: para archivos GRANDES (video, audio largo, PDF de muchas paginas)
# no conviene mandarlos en Base64 dentro de la peticion (cuenta para su limite de tamano).
# En su lugar tu funcion SUBE el archivo con la Files API y devuelve solo su "uri".
# La doc usa un xlsx y un video; aqui usamos un CSV pequeno (text/csv es un tipo admitido).

import json
from pathlib import Path

from google import genai

ASSETS = Path(__file__).resolve().parent.parent / "assets"

MODELOS = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite"]

client = genai.Client(http_options={"timeout": 60_000})

view_file_tool = {
    "type": "function",
    "name": "view_file",
    "description": "Opens a file from the local assets folder so it can be read, given its file name.",
    "parameters": {
        "type": "object",
        "properties": {"filename": {"type": "string", "description": "File name, e.g. ventas_q3.csv"}},
        "required": ["filename"],
    },
}

interaction = None
modelo_usado = None
for modelo in MODELOS:
    try:
        interaction = client.interactions.create(
            model=modelo,
            input="Open the file ventas_q3.csv and tell me which month had the highest sales and the total.",
            tools=[view_file_tool],
        )
        modelo_usado = modelo
        print(f"Modelo usado: {modelo}")
        break
    except Exception as e:
        print(f"[{modelo}] fallo: {type(e).__name__} {getattr(e, 'status_code', None)}")
if interaction is None:
    raise SystemExit("Ningun modelo respondio.")

tool_call = next(s for s in interaction.steps if s.type == "function_call")
print("El modelo pide:", tool_call.name, tool_call.arguments)

# TU funcion: sube el archivo a la Files API (queda guardado 48 h) y obtiene su uri
subido = client.files.upload(
    file=str(ASSETS / tool_call.arguments["filename"]),
    config={"mime_type": "text/csv"},
)
print("Archivo subido, uri:", subido.uri)

final_interaction = client.interactions.create(
    model=modelo_usado,
    previous_interaction_id=interaction.id,
    tools=[view_file_tool],
    input=[
        {
            "type": "function_result",
            "name": tool_call.name,
            "call_id": tool_call.id,
            "result": [
                {"type": "text", "text": json.dumps({"status": "ok"})},
                # bloque "document" con uri (en vez de data en Base64)
                {"type": "document", "uri": subido.uri, "mime_type": "text/csv"},
            ],
        }
    ],
)
print("\nRespuesta:", final_interaction.output_text)
