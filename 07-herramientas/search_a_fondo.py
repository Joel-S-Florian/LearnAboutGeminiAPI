# 07.19 Google Search a fondo (T5). Modelos 2.5 (la busqueda en Gemini 3 tiene cuota 0/0 en el nivel gratuito). La doc: pasos
# `google_search_call` (arguments.queries) y `google_search_result` (search_suggestions = HTML de sugerencias que hay que mostrar segun los
# terminos), anotaciones `url_citation` con start_index/end_index, y combinacion con code_execution/url_context/Maps/funciones (Gemini 3+).
# Se comprueba: estructura real, si los indices de las citas cuadran con el texto (incluso con acentos), cuantas busquedas hace segun el prompt,
# si decide NO buscar cuando no hace falta, idioma, y las combinaciones. Ejecutar con `python -u ... > archivo`.

import time

from google import genai

client = genai.Client(http_options={"api_version": "v1beta", "timeout": 120_000})
T = [{"type": "google_search"}]


def consultar(titulo, prompt, modelo="gemini-2.5-flash-lite", tools=T, detalle=False):
    t0 = time.time()
    try:
        r = client.interactions.create(model=modelo, input=prompt, tools=tools)
    except Exception as e:
        print(f"[{titulo}] FALLO {type(e).__name__} {getattr(e, 'status_code', None)} {str(e)[:230]}")
        return None
    llamadas = [s for s in r.steps if s.type == "google_search_call"]
    consultas = [q for s in llamadas for q in (getattr(s.arguments, "queries", None) or s.arguments.get("queries", []) if hasattr(s, "arguments") else [])]
    print(f"[{titulo}] {modelo} {time.time() - t0:.0f} s | pasos={[s.type for s in r.steps]} | busquedas={len(consultas)} {consultas[:4]} | tokens={r.usage.total_tokens}")
    texto, anot = "", []
    for s in r.steps:
        if s.type == "model_output":
            for b in s.content:
                if b.type == "text":
                    texto += b.text
                    anot += list(b.annotations or [])
    print(f"   texto: {texto[:200]!r}")
    print(f"   anotaciones: {len(anot)} | tipos={sorted({a.type for a in anot})}")
    if detalle:
        for s in r.steps:
            if s.type == "google_search_result":
                d = s.model_dump()
                print("   estructura google_search_result:", {k: (type(v).__name__, str(v)[:120]) for k, v in d.items() if v is not None})
        for s in llamadas[:1]:
            print("   estructura google_search_call:", {k: str(v)[:120] for k, v in s.model_dump().items() if v is not None})
        urls = [a.url for a in anot if hasattr(a, "url")]
        print("   dominios de las URLs citadas:", sorted({u.split('/')[2] for u in urls})[:6], "| URLs distintas:", len(set(urls)), "de", len(urls))
        print("   titulos:", sorted({a.title for a in anot if hasattr(a, 'title')})[:6])
        for a in anot[:3]:
            print(f"   cita [{a.start_index}:{a.end_index}] -> {texto[a.start_index:a.end_index]!r}")
        # ¿los indices cuadran? (la ultima cita deberia terminar dentro del texto)
        print("   indice maximo de las citas:", max((a.end_index for a in anot), default=None), "| longitud del texto:", len(texto))
    return r


print("=== 1) estructura (pregunta de la doc) ===")
consultar("Euro 2024", "Who won the euro 2024? Answer in two sentences.", detalle=True)
print("\n=== 2) en espanol, con acentos (¿cuadran los indices?) ===")
consultar("espanol", "¿Quién ganó la Eurocopa 2024 y cuál fue el marcador de la final? Responde en español con acentos.", detalle=True)
print("\n=== 3) ¿decide NO buscar si no hace falta? ===")
consultar("sin necesidad", "What is 17 * 23? Just the number.")
print("\n=== 4) pregunta compleja: ¿cuantas busquedas? ===")
consultar("compleja", "Compare the current weather in Tokyo and Santo Domingo, and also tell me who is the current UN Secretary-General. Be concise.")
print("\n=== 5) dato que cambia ===")
consultar("hoy", "What is today's date according to the web, and what is one top world news headline today? Be concise.")
print("\n=== 6) modelos: 2.5 flash y 2.0 flash ===")
consultar("2.5 flash", "Who won the euro 2024? One sentence.", modelo="gemini-2.5-flash")
consultar("2.0 flash", "Who won the euro 2024? One sentence.", modelo="gemini-2.0-flash")
print("\n=== 7) combinaciones en 2.5 ===")
consultar("search + code_execution", "Search for the population of Spain and compute 1% of it with code. One sentence.", tools=T + [{"type": "code_execution"}])
consultar("search + url_context", "Search for the Python language home page and read it. One sentence.", tools=T + [{"type": "url_context"}])
consultar("search + google_maps", "Find a cafe near the Eiffel Tower. One sentence.", tools=T + [{"type": "google_maps"}])
print("\n=== 8) Gemini 3.x (cuota) ===")
consultar("3.5 flash-lite", "Who won the euro 2024? One sentence.", modelo="gemini-3.5-flash-lite")
