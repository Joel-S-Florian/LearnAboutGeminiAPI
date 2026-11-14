# 04.8 TTS: usar el id de una voz de la biblioteca, DISENAR una voz con un prompt y REMEZCLAR otra (sin replicar).
#   A) id de una voz de la biblioteca (es-419-concierge-2, acento mexicano) como "voice" en speech_config
#   B) diseno: client.voices.create(voice={"type": "prompted", "prompted": {"input": <descripcion>}}, store=True)
#   C) remix: igual que B pero con prompted.base_voice = una voz existente; el input describe CAMBIOS relativos
# store=True guarda la voz en tu proyecto (maximo de voces activas; caduca tras 1 ano sin uso): por eso se BORRA al final.
# La replica de voz (type "replicated") exige grabaciones de referencia y de CONSENTIMIENTO de una persona: no se hace aqui.
# Cuota TTS gratuita: ~3 por minuto y ~10 por dia, asi que se espacian las llamadas.

import base64
import time
import wave
from pathlib import Path

from google import genai

SALIDAS = Path(__file__).resolve().parent.parent / "salidas"
SALIDAS.mkdir(exist_ok=True)
client = genai.Client(http_options={"api_version": "v1beta", "timeout": 120_000})
TEXTO = "Hola, bienvenido. ¿En qué te puedo ayudar hoy? Estoy aquí para lo que necesites."
voces_creadas = []


def sintetizar(nombre, voz):
    """Genera audio con la voz indicada (nombre o id) y lo guarda en salidas/. Devuelve una linea de resumen."""
    r = client.interactions.create(
        model="gemini-3.8-flash-tts",
        input=[{"type": "user_input", "content": [{"type": "text", "text": TEXTO}]}],
        response_format={"type": "audio"},
        generation_config={"speech_config": [{"voice": voz}]},
    )
    ruta = SALIDAS / f"voz_{nombre}.wav"
    ruta.write_bytes(base64.b64decode(r.output_audio.data))
    with wave.open(str(ruta), "rb") as w:
        seg = w.getnframes() / w.getframerate()
        return f"{ruta.name}: {ruta.stat().st_size} bytes, {seg:.1f} s, {w.getframerate()} Hz, {w.getnchannels()} canal(es)"


def crear_voz(nombre_visible, prompted, **extra):
    v = client.voices.create(
        voice={"type": "prompted", "display_name": nombre_visible, "language_code": "es-419", "prompted": prompted, **extra},
        store=True,  # obligatorio para voces "prompted"
    )
    voces_creadas.append(v.id)
    print(f"  voz creada: id={v.id} key={getattr(v, 'key', None)} tipo={v.type} nombre={v.display_name}")
    return v


try:
    # A) voz de la biblioteca por su id
    print("A:", sintetizar("biblioteca", "es-419-concierge-2"))
    time.sleep(25)

    # B) voz disenada
    b = crear_voz(
        "estudio-disenada",
        {"input": "A warm, calm adult woman with a Dominican Republic Caribbean Spanish accent, speaking at a relaxed, friendly pace."},
    )
    print("B:", sintetizar("disenada", b.id))
    time.sleep(25)

    # C) remix: partir de una voz predefinida (Kore) y pedir cambios relativos.
    # RESULTADO medido: en el nivel gratuito da 403 "Voice edit and remix requires Paid Quota Tier 1 or higher."
    try:
        c = crear_voz("estudio-remix", {"base_voice": "Kore", "input": "Make it noticeably lower in pitch and slower."})
        print("C:", sintetizar("remix", c.id))
    except Exception as e:
        print(f"C: remix NO disponible: {getattr(e, 'status_code', None)} {type(e).__name__}: {str(e)[:160]}")
finally:
    for vid in voces_creadas:
        try:
            # OJO: delete(id=...) quiere el id DESNUDO (voice_abc...). Con "voices/voice_abc..." da 404 y la voz
            # se queda guardada (la doc del SDK dice "resource name", pero el SDK ya antepone "voices/")
            client.voices.delete(id=vid.removeprefix("voices/"))
            print("  voz borrada:", vid)
        except Exception as e:
            print(f"  NO SE PUDO BORRAR {vid}: {type(e).__name__} {getattr(e, 'status_code', None)} {str(e)[:120]}")
    try:
        propias = [v.id for v in (client.voices.list(type_=["prompted"]).voices or [])]
        print("voces 'prompted' que quedan en el proyecto:", propias)
    except Exception as e:
        print(f"list de voces propias fallo: {type(e).__name__} {str(e)[:100]}")
