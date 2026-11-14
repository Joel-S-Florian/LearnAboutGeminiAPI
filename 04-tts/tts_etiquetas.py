# 04.3 TTS: texto en espanol + etiquetas inline + style
# Dos formas de controlar COMO suena, segun el alcance:
#   - style (en speech_metadata): vale para TODO el turno (emocion, ritmo, volumen)
#   - etiquetas <...> dentro del texto: valen para UN momento puntual (pausa, suspiro, tos)

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
        "content": [{
            "type": "text",
            # IDIOMA: no se configura, el modelo lo detecta del texto (aqui, espanol).
            # Las etiquetas van en INGLES aunque el texto no lo este (recomendacion de la doc).
            # Las MAYUSCULAS ponen enfasis en esa palabra.
            "text": "Hola, buenas tardes... <short pause> tengo una noticia MUY importante. <sigh> Por fin terminamos el proyecto.",
            "annotations": [{
                "type": "speech_metadata",
                # style: texto libre, aqui para todo el turno
                "style": "warm and excited",
            }],
        }],
    }],
    response_format={"type": "audio"},
    generation_config={"speech_config": [{"voice": "Kore"}]},
)

with open(SALIDAS / "out_etiquetas.wav", "wb") as f:
    f.write(base64.b64decode(interaction.output_audio.data))
print("Audio guardado en salidas/out_etiquetas.wav")
