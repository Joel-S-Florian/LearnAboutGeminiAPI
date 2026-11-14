# 04.4 TTS con streaming
# Con stream=True el audio llega en TROZOS (eventos) mientras se genera,
# en vez de esperar al audio completo. Util para empezar a reproducir antes.
# OJO: en streaming los trozos son PCM crudo (audio/l16, 24 kHz, mono, 16 bits),
# SIN cabecera WAV. Para guardarlos como .wav hay que ponerles la cabecera nosotros.

import base64
import wave
from pathlib import Path

from google import genai

# Carpeta de salidas junto a la raiz del repo (ignorada por git)
SALIDAS = Path(__file__).resolve().parent.parent / "salidas"
SALIDAS.mkdir(exist_ok=True)

client = genai.Client(http_options={"api_version": "v1beta"})

stream = client.interactions.create(
    model="gemini-3.8-flash-tts",
    input=[{
        "type": "user_input",
        "content": [{
            "type": "text",
            "text": "Have a wonderful day!",
            "annotations": [{"type": "speech_metadata", "style": "cheerful and friendly"}],
        }],
    }],
    response_format={"type": "audio"},
    generation_config={"speech_config": [{"voice": "Kore"}]},
    stream=True,  # DIFERENCIA CLAVE: devuelve un iterador de eventos, no una respuesta unica
)

trozos = []
for event in stream:
    # Cada evento "step.delta" con delta de tipo audio trae un trozo en Base64
    if event.event_type == "step.delta" and event.delta.type == "audio":
        trozos.append(base64.b64decode(event.delta.data))
print(f"Trozos de audio recibidos: {len(trozos)}")

# Unimos los trozos y escribimos la cabecera WAV con el modulo estandar "wave"
with wave.open(str(SALIDAS / "out_stream.wav"), "wb") as w:
    w.setnchannels(1)      # mono
    w.setsampwidth(2)      # 16 bits = 2 bytes por muestra
    w.setframerate(24000)  # 24 kHz
    w.writeframes(b"".join(trozos))
print("Audio guardado en salidas/out_stream.wav")
