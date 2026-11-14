# 04.5 TTS: formatos de salida
# Por defecto (sin stream) el audio llega como WAV con cabecera. Con
# response_format.mime_type se puede pedir otro formato, y con sample_rate otra frecuencia:
#   audio/l16   PCM crudo de 16 bits, sin cabecera (por defecto 24 kHz)
#   audio/mulaw G.711 mu-law, telefonia (America del Norte y Japon), 8 kHz
#   audio/alaw  G.711 A-law, telefonia (Europa e internacional), 8 kHz

import base64
from pathlib import Path

from google import genai

# Carpeta de salidas junto a la raiz del repo (ignorada por git)
SALIDAS = Path(__file__).resolve().parent.parent / "salidas"
SALIDAS.mkdir(exist_ok=True)

client = genai.Client(http_options={"api_version": "v1beta"})

# (mime_type, sample_rate, extension del archivo)
FORMATOS = [
    ("audio/l16", 24000, "pcm"),
    ("audio/mulaw", 8000, "mulaw"),
    ("audio/alaw", 8000, "alaw"),
]

for mime, rate, ext in FORMATOS:
    interaction = client.interactions.create(
        model="gemini-3.8-flash-tts",
        input=[{
            "type": "user_input",
            "content": [{
                "type": "text",
                "text": "Have a wonderful day!",
                "annotations": [{"type": "speech_metadata", "style": "cheerful and friendly"}],
            }],
        }],
        # Antes era solo {"type": "audio"}; ahora le anadimos formato y frecuencia
        response_format={"type": "audio", "mime_type": mime, "sample_rate": rate},
        generation_config={"speech_config": [{"voice": "Kore"}]},
    )
    datos = base64.b64decode(interaction.output_audio.data)
    (SALIDAS / f"out_formato.{ext}").write_bytes(datos)
    # Un WAV empieza por los bytes "RIFF"; los formatos crudos no tienen cabecera
    print(f"{mime} @ {rate} Hz: {len(datos)} bytes, empieza con RIFF: {datos[:4] == b'RIFF'}")
