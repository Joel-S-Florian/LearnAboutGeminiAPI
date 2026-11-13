# 7.2 TTS con dos hablantes
# Mismo esquema que tts.py, pero con dos voces dialogando en un solo audio.

import base64

from pathlib import Path

from google import genai

# Carpeta de salidas junto a la raiz del repo (ignorada por git)
SALIDAS = Path(__file__).resolve().parent.parent / "salidas"
SALIDAS.mkdir(exist_ok=True)

client = genai.Client(http_options={"api_version": "v1beta"})

interaction = client.interactions.create(
    model="gemini-3.8-flash-tts",
    input=[{
        "type": "user_input",
        # Un bloque de texto POR TURNO de cada hablante (antes habia solo uno)
        "content": [
            {
                "type": "text",
                "text": "How's it going today Jane?",
                # speaker: quien habla (debe coincidir con el nombre en speech_config);
                # style: como lo dice, solo para este turno
                "annotations": [{
                    "type": "speech_metadata",
                    "speaker": "Joe",
                    "style": "cheerful and friendly",
                }],
            },
            {
                "type": "text",
                "text": "Not too bad, how about you? Ready to test these new voices?",
                "annotations": [{
                    "type": "speech_metadata",
                    "speaker": "Jane",
                    "style": "calm and relaxed",
                }],
            },
        ],
    }],
    response_format={"type": "audio"},
    # DIFERENCIA CLAVE: con un hablante speech_config era una LISTA ([{"voice": ...}]);
    # con varios es un OBJETO con la clave "speakers", que enlaza cada nombre con una voz
    generation_config={
        "speech_config": {
            "speakers": [
                {"speaker": "Joe", "voice": "Puck"},
                {"speaker": "Jane", "voice": "Kore"},
            ],
        }
    },
)

with open(SALIDAS / "out_dialogo.wav", "wb") as f:
    f.write(base64.b64decode(interaction.output_audio.data))
print("Audio guardado en salidas/out_dialogo.wav")
