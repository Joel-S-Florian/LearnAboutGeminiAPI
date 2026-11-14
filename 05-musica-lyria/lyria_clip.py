# 05.1 Lyria 3: generar un clip de musica (30 segundos)
# lyria-3-clip-preview siempre genera clips de 30 s en MP3 (44.1 kHz, estereo).
# Misma API nueva (interactions.create); aqui input es un str con la descripcion musical.

import base64
from pathlib import Path

from google import genai

# Carpeta de salidas junto a la raiz del repo (ignorada por git)
SALIDAS = Path(__file__).resolve().parent.parent / "salidas"
SALIDAS.mkdir(exist_ok=True)

# Los modelos de Lyria solo existen en la version v1beta de la API. Con la version por
# defecto da 404 "model not found" (comprobado: models.list() daba 28 modelos sin Lyria;
# con v1beta da 64, incluidos lyria-3-clip-preview y lyria-3.5)
client = genai.Client(http_options={"api_version": "v1beta"})

interaction = client.interactions.create(
    model="lyria-3-clip-preview",
    input="A short instrumental acoustic guitar piece.",
)

# La respuesta trae dos cosas: el audio (Base64) y un texto con la letra y la estructura.
# output_audio devuelve el ultimo bloque de audio; output_text, el texto.
audio = interaction.output_audio
if audio:
    with open(SALIDAS / "music.mp3", "wb") as f:
        f.write(base64.b64decode(audio.data))
    print("Musica guardada en salidas/music.mp3")
else:
    print("No llego audio.")

texto = interaction.output_text
if texto:
    print(f"Letra / estructura:\n{texto}")
