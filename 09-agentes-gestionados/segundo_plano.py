# 09.10 Ejecucion en segundo plano: con background=True la llamada vuelve AL INSTANTE con un id y el
# agente sigue trabajando en Google. Tu codigo hace "polling" (client.interactions.get) hasta que el
# estado deje de ser "in_progress". Requiere store=True (que es el valor por defecto).
# Tambien se puede CANCELAR una interaccion en curso con client.interactions.cancel(id=...).
# Casos:
#   A) tarea corta en segundo plano + polling, mostrando que estados se ven y cuanto tarda
#   B) tarea lenta (cuenta con pausas) que cancelamos a los ~10 s; vemos el estado resultante

import time

from google import genai

client = genai.Client(http_options={"api_version": "v1beta", "timeout": 300_000})
AGENTE = "antigravity-preview-09-2026"
CONFIG = {"type": "antigravity", "model": "gemini-3.5-flash-lite", "max_total_tokens": 30_000}


def esperar(interaccion, maximo_s=240, cada_s=5):
    """Polling: pregunta por la interaccion hasta que deje de estar en curso. Devuelve (interaccion, estados_vistos)."""
    estados = [interaccion.status]
    t0 = time.time()
    while interaccion.status == "in_progress" and time.time() - t0 < maximo_s:
        time.sleep(cada_s)
        interaccion = client.interactions.get(id=interaccion.id)
        estados.append(interaccion.status)
    return interaccion, estados


# --- A: segundo plano + polling ---
t0 = time.time()
a = client.interactions.create(
    agent=AGENTE,
    input="Write the first 20 Fibonacci numbers to fibonacci.txt, then tell me their sum. Reply in one line.",
    environment="remote",
    agent_config=CONFIG,
    background=True,
)
print(f"A: devuelta en {time.time() - t0:.1f} s con estado inicial = {a.status!r}, id = {a.id[:24]}...")
a, estados = esperar(a)
print(f"A: estados vistos = {estados}")
print(f"A: final = {a.status!r} tras {time.time() - t0:.0f} s")
print("A: salida:", (a.output_text or "(sin texto)").strip()[:200])

# --- B: cancelar ---
b = client.interactions.create(
    agent=AGENTE,
    input="In bash, print the numbers 1 to 12, waiting 5 seconds between each (use sleep 5). Then say done.",
    environment="remote",
    agent_config=CONFIG,
    background=True,
)
print(f"\nB: iniciada, estado = {b.status!r}")
time.sleep(10)
try:
    resp = client.interactions.cancel(id=b.id)
    print("B: cancel() devolvio estado =", getattr(resp, "status", resp))
except Exception as e:
    print(f"B: cancel fallo: {type(e).__name__} {getattr(e, 'status_code', None)} {str(e)[:250]}")
time.sleep(3)
b = client.interactions.get(id=b.id)
print("B: estado despues de cancelar =", b.status)
