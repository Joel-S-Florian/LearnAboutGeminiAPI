# 07.8 computer_use: que formato de function_result acepta el modelo? (el bucle dio 400 "safety violations")
# Se hace UNA primera llamada y se prueban varias formas de devolver el resultado, con la misma captura.
import base64
from pathlib import Path

from google import genai

SAL = Path(__file__).resolve().parent.parent / "salidas" / "computer_use"
img = base64.b64encode((SAL / "paso_01.png").read_bytes()).decode()
client = genai.Client(http_options={"timeout": 90_000})
TOOLS = [{"type": "computer_use", "environment": "browser"}]
MODELO = "gemini-3.5-flash-lite"

IMG = {"type": "image", "mime_type": "image/png", "data": img}
VARIANTES = {
    "solo_imagen": [IMG],
    "texto_e_imagen": [{"type": "text", "text": "OK"}, IMG],
    "solo_texto": [{"type": "text", "text": "OK, page loaded."}],
    "cadena": "OK",
}
for nombre, result in VARIANTES.items():
    try:
        i = client.interactions.create(model=MODELO, tools=TOOLS, input="Go to https://docs.python.org/3/ and tell me the title of the page.")
        c = next(s for s in i.steps if s.type == "function_call")
        f = client.interactions.create(
            model=MODELO, previous_interaction_id=i.id, tools=TOOLS,
            input=[{"type": "function_result", "name": c.name, "call_id": c.id, "result": result}],
        )
        print(f"[{nombre}] OK ->", [s.type for s in f.steps], str(f.output_text)[:100].replace("\n", " "))
    except Exception as e:
        print(f"[{nombre}] fallo: {getattr(e, 'status_code', None)} {str(e)[:130]}")
