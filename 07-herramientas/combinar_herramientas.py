# 07.7 Combinar herramientas INTEGRADAS (las ejecuta Google) con TUS funciones (las ejecutas tu) en una misma interaccion.
# Segun la doc (preview, Gemini 3+) esto funciona por "circulacion de contexto": el servidor conserva los pasos de la herramienta
# integrada y los expone; cada paso lleva `id` y `signature` (contexto cifrado). Con previous_interaction_id (con estado) el servidor
# lo maneja solo; sin estado hay que devolver id Y signature. Limitacion: `tool_choice="auto"` NO esta soportado; usar "validated".
# Casos:
#   1 url_context + funcion, CON estado          2 igual, SIN estado (historial completo)    3 SIN estado quitando las `signature`
#   4 tool_choice auto vs validated              5 file_search + funcion                     6 google_search + funcion (2.5 y 3.x)
# google_search en 3.x tiene cuota 0/0 en el nivel gratuito; por eso se usa url_context como herramienta integrada principal.
# Ejecutar con `python -u ... > archivo`. Las signature son cifradas y largas: solo se imprime su longitud.

import copy
import json
import time
from pathlib import Path

from google import genai

ASSETS = Path(__file__).resolve().parent.parent / "assets"
client = genai.Client(http_options={"api_version": "v1beta", "timeout": 90_000})
MODELO = "gemini-3.5-flash-lite"

GUARDAR = {
    "type": "function", "name": "guardar_resultado",
    "description": "Saves a short text result (for example a page title or a secret word) in the user's notebook.",
    "parameters": {"type": "object", "properties": {"texto": {"type": "string", "description": "The text to save"}}, "required": ["texto"]},
}
PROMPT_URL = "Use your URL tool to read https://example.com, then call guardar_resultado with the page title. Finish by telling me what you saved."


def resumen(steps):
    out = []
    for s in steps or []:
        d = s.model_dump()
        out.append(f"{s.type}" + (f"[id:{'si' if d.get('id') else 'no'} sig:{len(d['signature']) if d.get('signature') else 0}]" if s.type != "model_output" else ""))
    return out


def ejecutar(r):
    """Ejecuta MIS funciones (function_call) y devuelve los function_result."""
    res = []
    for s in r.steps or []:
        if s.type == "function_call":
            print(f"   mi funcion: {s.name}({s.arguments})")
            res.append({"type": "function_result", "name": s.name, "call_id": s.id,
                        "result": [{"type": "text", "text": json.dumps({"guardado": True})}]})
    return res


def crear(**kw):
    try:
        return client.interactions.create(model=MODELO, **kw)
    except Exception as e:
        print(f"   FALLO: {type(e).__name__} {getattr(e, 'status_code', None)} {str(e)[:260]}")
        return None


def caso_con_estado(titulo, tools, prompt, **extra):
    print(f"\n===== {titulo} =====")
    r = crear(input=prompt, tools=tools, **extra)
    prev = None
    for turno in range(1, 5):
        if r is None:
            return
        print(f"  turno {turno}: {resumen(r.steps)}")
        res = ejecutar(r)
        if not res:
            print("  FINAL:", (r.output_text or "")[:260].replace("\n", " "))
            return
        prev = r.id
        r = crear(input=res, tools=tools, previous_interaction_id=prev, **extra)


def caso_sin_estado(titulo, tools, prompt, quitar_signature=False):
    print(f"\n===== {titulo} =====")
    historial = [{"type": "user_input", "content": [{"type": "text", "text": prompt}]}]
    for turno in range(1, 5):
        r = crear(input=copy.deepcopy(historial), tools=tools, store=False)
        if r is None:
            return
        print(f"  turno {turno}: {resumen(r.steps)}")
        res = ejecutar(r)
        if not res:
            print("  FINAL:", (r.output_text or "")[:260].replace("\n", " "))
            return
        pasos = [s.model_dump() for s in r.steps]
        if quitar_signature:
            for p in pasos:
                p.pop("signature", None)
        historial += pasos + res


URL = [{"type": "url_context"}, GUARDAR]
caso_con_estado("1 url_context + funcion, CON estado", URL, PROMPT_URL)
caso_sin_estado("2 url_context + funcion, SIN estado (historial completo)", URL, PROMPT_URL)
caso_sin_estado("3 SIN estado y SIN signature", URL, PROMPT_URL, quitar_signature=True)
for modo in ("auto", "validated"):
    caso_con_estado(f"4 tool_choice={modo}", URL, PROMPT_URL, generation_config={"tool_choice": modo})

# 5) file_search + funcion (store con el embedding por defecto; se borra en finally)
store = client.file_search_stores.create(config={"display_name": "combinar-notas"})
try:
    op = client.file_search_stores.upload_to_file_search_store(
        file=str(ASSETS / "sample_notas.txt"), file_search_store_name=store.name, config={"display_name": "notas"})
    while not op.done:
        time.sleep(5)
        op = client.operations.get(op)
    time.sleep(5)
    caso_con_estado("5 file_search + funcion", [{"type": "file_search", "file_search_store_names": [store.name]}, GUARDAR],
                    "Search my notes for the secret word of the File Search experiment, then call guardar_resultado with that word. Finish by telling me the word.")
finally:
    client.file_search_stores.delete(name=store.name, config={"force": True})
    print("   store borrado")

# 6) google_search + funcion: 3.x (cuota 0/0 gratis) y 2.5 (la doc dice que la combinacion es de Gemini 3+)
for modelo in ("gemini-3.5-flash-lite", "gemini-2.5-flash-lite"):
    MODELO = modelo
    caso_con_estado(f"6 google_search + funcion con {modelo}", [{"type": "google_search"}, GUARDAR],
                    "Search the web for the capital of Australia, then call guardar_resultado with it. Finish by telling me what you saved.")
