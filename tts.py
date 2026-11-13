# 7. Text-to-speech (TTS) - un solo hablante
# Los modelos TTS reciben SOLO texto y devuelven SOLO audio.
# Se les da el texto exacto a leer (transcripcion literal); el estilo va aparte.

import base64

from google import genai

# La documentacion de TTS usa la version v1beta de la API, por eso la pedimos
client = genai.Client(http_options={"api_version": "v1beta"})

interaction = client.interactions.create(
    model="gemini-3.8-flash-tts",
    # Aqui input es una lista de "turnos": un turno de tipo user_input con su contenido
    input=[{
        "type": "user_input",
        "content": [{
            "type": "text",
            # Texto que se va a leer, tal cual (no pongas instrucciones aqui o las leera)
            "text": "Have a wonderful day!",
            # annotations: metadatos del turno; speech_metadata.style controla COMO se dice
            "annotations": [{
                "type": "speech_metadata",
                "style": "cheerful and friendly",
            }],
        }],
    }],
    # response_format le dice al modelo que tipo de salida queremos: audio
    response_format={"type": "audio"},
    # speech_config: la voz. Es una LISTA con un elemento para un hablante
    # ("Kore" es una de las voces predefinidas)
    generation_config={"speech_config": [{"voice": "Kore"}]},
)

# output_audio devuelve el ultimo bloque de audio; viene en Base64.
# En peticiones normales (sin stream) llega como WAV completo, asi que se guarda directo
with open("out.wav", "wb") as f:
    f.write(base64.b64decode(interaction.output_audio.data))
print("Audio guardado en out.wav")
