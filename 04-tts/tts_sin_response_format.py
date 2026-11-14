# 04.9 TTS sin response_format: en tts.py siempre pusimos response_format={"type": "audio"} "por si acaso".
# Pregunta pendiente: es obligatorio? Se hace la misma peticion QUITANDOLO y se mira que llega.

import base64
import wave
from pathlib import Path

from google import genai

SALIDAS = Path(__file__).resolve().parent.parent / "salidas"
SALIDAS.mkdir(exist_ok=True)
client = genai.Client(http_options={"api_version": "v1beta", "timeout": 120_000})

try:
    r = client.interactions.create(
        model="gemini-3.8-flash-tts",
        input=[{"type": "user_input", "content": [{"type": "text", "text": "Have a wonderful day!"}]}],
        # SIN response_format
        generation_config={"speech_config": [{"voice": "Kore"}]},
    )
except Exception as e:
    raise SystemExit(f"RECHAZADO sin response_format: {getattr(e, 'status_code', None)} {type(e).__name__}: {str(e)[:250]}")

audio = r.output_audio
print("estado:", r.status, "| hay audio:", bool(audio), "| mime:", getattr(audio, "mime_type", None))
if audio:
    ruta = SALIDAS / "sin_response_format.wav"
    ruta.write_bytes(base64.b64decode(audio.data))
    with wave.open(str(ruta), "rb") as w:
        print(f"{ruta.name}: {ruta.stat().st_size} bytes, {w.getnframes() / w.getframerate():.1f} s, {w.getframerate()} Hz")
