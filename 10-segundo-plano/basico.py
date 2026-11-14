# 10.1 a 10.4 Segundo plano con MODELOS normales (en 09.10 lo hicimos con un agente): background=True hace que la
# llamada vuelva enseguida con un id y la tarea siga en el servidor; tu codigo consulta con interactions.get(id).
# Estados posibles: in_progress, requires_action, completed, failed, cancelled.
# Casos de este script:
#   A) crear en segundo plano + polling (que estados se ven, cuanto tarda)
#   B) background=True con store=False -> la doc dice 400 (el servidor debe GUARDAR la interaccion mientras haces polling)
#   C) encadenar con previous_interaction_id a una interaccion AUN en curso -> la doc dice 400; despues de completarse, si
# Al final se BORRAN las interacciones creadas (plan gratuito: se conservan 1 dia).

import time

from google import genai

MODELOS = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.8-flash"]
client = genai.Client(http_options={"timeout": 120_000})
creadas = []
PROMPT = "Write a detailed analysis (about 400 words) of the impact of artificial intelligence on modern healthcare."


def crear(**kw):
    """Prueba los modelos en orden; devuelve (modelo, interaccion)."""
    for m in MODELOS:
        try:
            r = client.interactions.create(model=m, **kw)
            creadas.append(r.id)
            return m, r
        except Exception as e:
            ultimo = e
            print(f"  [{m}] fallo: {type(e).__name__} {getattr(e, 'status_code', None)} {str(e)[:120]}")
    raise ultimo


def esperar(r, maximo_s=120):
    estados, t0 = [r.status], time.time()
    while r.status == "in_progress" and time.time() - t0 < maximo_s:
        time.sleep(2)
        r = client.interactions.get(id=r.id)
        estados.append(r.status)
    return r, estados


try:
    # --- A: segundo plano + polling ---
    t0 = time.time()
    modelo, a = crear(input=PROMPT, background=True)
    print(f"A: devuelta en {time.time() - t0:.1f} s con estado {a.status!r} (modelo {modelo})")
    a, estados = esperar(a)
    print(f"A: estados = {estados} | final = {a.status!r} tras {time.time() - t0:.0f} s")
    if a.status == "failed":
        print("A: error =", getattr(a, "error", None))
    print(f"A: salida = {len((a.output_text or '').split())} palabras | primeras palabras: {(a.output_text or '')[:100]!r}")

    # --- B: store=False ---
    try:
        client.interactions.create(model=modelo, input="Say hi.", background=True, store=False)
        print("B: ACEPTADO background=True con store=False (la doc dice 400)")
    except Exception as e:
        print(f"B: RECHAZADO {getattr(e, 'status_code', None)}: {str(e)[:200]}")

    # --- C: encadenar a una interaccion en curso ---
    _, larga = crear(input=PROMPT, background=True)
    try:
        client.interactions.create(model=modelo, input="Now summarize that in one line.", previous_interaction_id=larga.id)
        print("C: encadenar a una en curso fue ACEPTADO (la doc dice 400)")
    except Exception as e:
        print(f"C: encadenar a una en curso -> RECHAZADO {getattr(e, 'status_code', None)}: {str(e)[:200]}")
    larga, _ = esperar(larga)
    print("C: la primera termino con estado", larga.status)
    seg = client.interactions.create(
        model=modelo, input="Now summarize that in one line.", previous_interaction_id=larga.id
    )
    creadas.append(seg.id)
    print("C: encadenada tras completarse ->", (seg.output_text or "").strip()[:150])
finally:
    for i in creadas:
        try:
            client.interactions.delete(id=i)
        except Exception as e:
            print(f"  no se pudo borrar {i[:12]}...: {type(e).__name__}")
    print(f"Borradas {len(creadas)} interacciones")
