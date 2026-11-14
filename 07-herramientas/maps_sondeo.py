# 07.21 Google Maps (T7): sondeo. La cuota gratuita de Maps es 0/0 (429 en pruebas anteriores), asi que se prueba (a) cada modelo que la doc lista,
# por si alguno la tiene disponible, y (b) la VALIDACION de parametros, que se comprueba antes de la cuota. Ejecutar con `python -u ... > archivo`.
from google import genai

client = genai.Client(http_options={"api_version": "v1beta", "timeout": 25_000})
P = "What are the best Italian restaurants within a 15-minute walk from here?"


def probar(titulo, modelo, herramienta):
    try:
        r = client.interactions.create(model=modelo, input=P, tools=[herramienta])
    except Exception as e:
        print(f"[{titulo}] {getattr(e, 'status_code', None)} {type(e).__name__}: {str(e)[:210]}")
        return
    anot = [a for s in r.steps if s.type == "model_output" for b in s.content if b.type == "text" for a in (b.annotations or [])]
    print(f"[{titulo}] FUNCIONO. pasos={[s.type for s in r.steps]} anotaciones={[(a.type) for a in anot][:4]}")
    for a in anot[:2]:
        print("   ", {k: str(v)[:80] for k, v in a.model_dump().items() if v is not None})


MAPS = {"type": "google_maps", "latitude": 34.050481, "longitude": -118.248526}
for m in ("gemini-2.5-flash-lite", "gemini-2.5-flash", "gemini-2.5-pro"):  # los 3.x ya dieron 429 en la primera ejecucion
    probar(f"modelo {m}", m, MAPS)
print("--- validacion de parametros (modelo 3.5 flash-lite) ---")
probar("sin coordenadas", "gemini-3.5-flash-lite", {"type": "google_maps"})
probar("latitud 200", "gemini-3.5-flash-lite", {**MAPS, "latitude": 200})
probar("latitud texto", "gemini-3.5-flash-lite", {**MAPS, "latitude": "abc"})
probar("campo desconocido", "gemini-3.5-flash-lite", {**MAPS, "radio_km": 5})
