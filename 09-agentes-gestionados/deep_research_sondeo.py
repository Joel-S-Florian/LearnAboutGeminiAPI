# SIN RESULTADO (2026-11-14): la primera ejecucion se colgo >6 min y hubo que matarla; como la salida pasaba por un `grep`
# (bufer), no se imprimio nada y NO se sabe si llego a crear la investigacion. E4 se salto por decision de Joel. Si se retoma:
# ejecutar con `python -u` y redirigiendo a un archivo, y poner timeouts mas cortos.
# 09.32 Deep Research, sondeo de acceso: ¿puede este proyecto usar el agente `deep-research-preview-04-2026`?
# La doc estima 1-3 USD por tarea (Max: 3-7) y NO muestra un tope de tokens configurable, asi que NO se deja correr una investigacion:
# se arranca con una pregunta minima y se CANCELA en cuanto se vea el estado (maximo ~15 s). Si el nivel gratuito no lo permite,
# lo esperable es un error 4xx al crearla y no se gasta nada. Se registra todo (estado, error, tokens usados hasta cancelar).
# Siempre se intenta cancelar y borrar la interaccion en finally.

import time

from google import genai

client = genai.Client(http_options={"api_version": "v1beta", "timeout": 60_000})
AGENTE = "deep-research-preview-04-2026"
iid = None

try:
    t0 = time.time()
    try:
        r = client.interactions.create(
            agent=AGENTE, background=True,
            input="In one short paragraph: in what year was the Python programming language first released?",
        )
    except Exception as e:
        raise SystemExit(f"NO SE PUDO CREAR: {type(e).__name__} {getattr(e, 'status_code', None)} {str(e)[:400]}")
    iid = r.id
    print(f"creada en {time.time() - t0:.1f} s | id={iid} | estado inicial={r.status}")

    for _ in range(3):  # ~15 s de observacion, no mas
        time.sleep(5)
        r = client.interactions.get(id=iid)
        print(f"  +{time.time() - t0:.0f} s estado={r.status} pasos={[getattr(s, 'type', None) for s in r.steps or []]}")
        if r.status != "in_progress":
            break
    if r.status in ("in_progress", "queued"):
        c = client.interactions.cancel(id=iid)
        print("cancel() ->", getattr(c, "status", c))
        time.sleep(5)
        r = client.interactions.get(id=iid)
    print("estado final:", r.status, "| tokens:", getattr(getattr(r, "usage", None), "total_tokens", "?"),
          "| error:", str(getattr(r, "error", None))[:200])
finally:
    if iid:
        try:
            client.interactions.delete(id=iid)
            print("interaccion borrada")
        except Exception as e:
            print("no se pudo borrar:", getattr(e, "status_code", None), str(e)[:100])
