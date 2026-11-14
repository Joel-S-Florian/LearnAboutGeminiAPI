# 10.6 Cancelar y borrar:
#   cancel (POST /interactions/{id}/cancel): detiene la tarea en curso -> estado "cancelled" (puede tardar un poco)
#   delete (DELETE /interactions/{id}):      borra el registro; un get posterior debe dar 404
# Prueba: tarea larga -> cancelar a los 2 s -> ver estado; borrar -> get debe dar 404.
# Tambien se prueba cancelar una interaccion que YA termino, y borrar una que no existe.

import time

from google import genai

MODELOS = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.8-flash"]
client = genai.Client(http_options={"timeout": 120_000})
PROMPT = "Write an extremely detailed essay (at least 3000 words) about the history of mathematics."


def crear():
    for m in MODELOS:
        try:
            return client.interactions.create(model=m, input=PROMPT, background=True)
        except Exception as e:
            print(f"[{m}] fallo: {type(e).__name__} {getattr(e, 'status_code', None)}")
    raise SystemExit("Ningun modelo respondio.")


def estado_tras(id_, espera=0):
    time.sleep(espera)
    return client.interactions.get(id=id_).status


a = crear()
print("A: creada, estado", a.status)
time.sleep(2)
try:
    c = client.interactions.cancel(id=a.id)
    print("A: cancel() devolvio estado =", getattr(c, "status", c))
except Exception as e:
    print(f"A: cancel fallo: {type(e).__name__} {getattr(e, 'status_code', None)} {str(e)[:150]}")
print("A: estado tras 4 s =", estado_tras(a.id, 4))
print("A: ¿salida parcial?", len(client.interactions.get(id=a.id).output_text or ""), "caracteres")

# Borrar y comprobar el 404
client.interactions.delete(id=a.id)
try:
    client.interactions.get(id=a.id)
    print("A: tras borrar, get SIGUE funcionando (la doc dice 404)")
except Exception as e:
    print(f"A: tras borrar, get -> {getattr(e, 'status_code', None)} {type(e).__name__}")

# Cancelar una interaccion YA terminada
b = client.interactions.create(model=a.model if getattr(a, "model", None) else MODELOS[0], input="Say hi in one word.", background=True)
time.sleep(8)
print("B: estado antes de cancelar =", estado_tras(b.id))
try:
    c = client.interactions.cancel(id=b.id)
    print("B: cancel sobre una completada ->", getattr(c, "status", c))
except Exception as e:
    print(f"B: cancel sobre una completada -> {getattr(e, 'status_code', None)} {type(e).__name__}: {str(e)[:150]}")
print("B: estado despues =", estado_tras(b.id))
client.interactions.delete(id=b.id)

# Borrar algo que no existe
try:
    client.interactions.delete(id="v1_noexiste")
    print("C: borrar un id inexistente no dio error")
except Exception as e:
    print(f"C: borrar un id inexistente -> {getattr(e, 'status_code', None)} {type(e).__name__}")
