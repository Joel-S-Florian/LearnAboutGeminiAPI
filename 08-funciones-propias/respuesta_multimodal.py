# 08.10 Respuestas multimodales de una funcion: tu function_result puede llevar IMAGENES (y PDF, audio,
# video...), no solo texto. El modelo las "ve" en el turno siguiente. Solo modelos Gemini 3+.
# Cada bloque de media lleva su "type" y su mime_type, y los datos en Base64 ("data") o un "uri".
# Aqui: el modelo pide "get_image" y tu funcion le devuelve assets/sample.jpg.

import base64
import json
from pathlib import Path

from google import genai

ASSETS = Path(__file__).resolve().parent.parent / "assets"

MODELOS = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite"]

client = genai.Client(http_options={"timeout": 60_000})

get_image_tool = {
    "type": "function",
    "name": "get_image",
    "description": "Returns an image file from the local assets folder, given its file name.",
    "parameters": {
        "type": "object",
        "properties": {"filename": {"type": "string", "description": "The image file name, e.g. sample.jpg"}},
        "required": ["filename"],
    },
}

interaction = None
modelo_usado = None
for modelo in MODELOS:
    try:
        interaction = client.interactions.create(
            model=modelo,
            input="Get the image named sample.jpg and describe what you see in it.",
            tools=[get_image_tool],
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

# TU funcion: lee el archivo y lo codifica en Base64 (igual que en el tema 02)
ruta = ASSETS / tool_call.arguments["filename"]
base64_image = base64.b64encode(ruta.read_bytes()).decode("utf-8")

final_interaction = client.interactions.create(
    model=modelo_usado,
    previous_interaction_id=interaction.id,
    tools=[get_image_tool],
    input=[
        {
            "type": "function_result",
            "name": tool_call.name,
            "call_id": tool_call.id,
            # result es una LISTA de bloques: puedes mezclar texto e imagen
            "result": [
                {"type": "text", "text": ruta.name},
                {"type": "image", "mime_type": "image/jpeg", "data": base64_image},
            ],
        }
    ],
)
print("\nDescripcion del modelo:", final_interaction.output_text)
