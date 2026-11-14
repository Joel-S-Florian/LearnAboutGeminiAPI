# 10.5 Streaming de una interaccion en segundo plano CON RECONEXION: cada evento trae un event_id; si se corta
# la conexion, client.interactions.get(id, stream=True, last_event_id=<ultimo>) retoma el flujo desde ese evento.
# Prueba: arrancamos una tarea larga, leemos unos trozos de texto, CORTAMOS a proposito, reconectamos con el
# ultimo event_id y comprobamos que parte1 + parte2 == texto final (sin huecos ni repeticiones).

from collections import Counter

from google import genai

MODELOS = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.8-flash"]
client = genai.Client(http_options={"timeout": 120_000})
PROMPT = "Write a detailed essay (about 700 words) on the history of the internet, in five paragraphs."

interaccion = None
for m in MODELOS:
    try:
        interaccion = client.interactions.create(model=m, input=PROMPT, background=True)
        print(f"Modelo {m}, estado inicial {interaccion.status!r}")
        break
    except Exception as e:
        print(f"[{m}] fallo: {type(e).__name__} {getattr(e, 'status_code', None)}")
if interaccion is None:
    raise SystemExit("Ningun modelo respondio.")

try:
    parte1, ultimo_id, tipos = [], None, Counter()
    # Primera conexion: leer unos cuantos trozos y cortar
    for ev in client.interactions.get(id=interaccion.id, stream=True):
        tipos[ev.event_type] += 1
        if getattr(ev, "event_id", None):
            ultimo_id = ev.event_id
        if ev.event_type == "step.delta" and ev.delta.type == "text":
            parte1.append(ev.delta.text)
            # La 1a prueba (corte tras 5 trozos) NUNCA llego a cortar: el texto llego en solo 4 trozos grandes
            # (~1500 caracteres cada uno) y el stream termino solo. Por eso se corta tras el 2o trozo.
            if len(parte1) >= 2:
                print("-- corte simulado tras 2 trozos de texto; ultimo event_id =", str(ultimo_id)[:40])
                break
    print("Eventos vistos en la 1a conexion:", dict(tipos))

    # Reconexion desde el ultimo evento recibido
    parte2, tipos2, completado = [], Counter(), False
    for ev in client.interactions.get(id=interaccion.id, stream=True, last_event_id=ultimo_id):
        tipos2[ev.event_type] += 1
        if ev.event_type == "step.delta" and ev.delta.type == "text":
            parte2.append(ev.delta.text)
        if ev.event_type == "interaction.completed":
            completado = True
            break
    print("Eventos vistos tras reconectar:", dict(tipos2), "| completado:", completado)

    final = client.interactions.get(id=interaccion.id).output_text or ""
    unido = "".join(parte1) + "".join(parte2)
    print(f"Texto: parte1={len(''.join(parte1))} car, parte2={len(''.join(parte2))} car, unido={len(unido)} car, final={len(final)} car")
    print("¿parte1 + parte2 == texto final?", unido == final)
    if unido != final:
        print("  empieza igual:", unido[:60] == final[:60], "| unido termina con:", repr(unido[-40:]), "| final termina con:", repr(final[-40:]))
finally:
    try:
        client.interactions.delete(id=interaccion.id)
        print("Interaccion borrada")
    except Exception as e:
        print(f"no se pudo borrar: {type(e).__name__}")
