# 5. Multimodal understanding
# Los modelos Gemini entienden imagenes, audio, video y documentos de forma nativa.
# Se pasa el contenido junto al texto en UNA sola peticion.
# Aqui: una imagen local (Base64) + un audio (subido a la Files API) en la misma llamada.

import base64
import random
import time
import urllib.request

from pathlib import Path

from google import genai

# Rutas relativas a ESTE archivo: el script funciona ejecutado desde cualquier carpeta
RAIZ = Path(__file__).resolve().parent.parent
ASSETS = RAIZ / "assets"    # archivos de entrada (sample.jpg)
SALIDAS = RAIZ / "salidas"  # archivos generados/descargados (ignorados por git)
SALIDAS.mkdir(exist_ok=True)
AUDIO_PATH = SALIDAS / "sample_audio.mp3"

# Igual que en pregunta_gemini.py: el SDK busca la variable de entorno GEMINI_API_KEY
client = genai.Client()

# Modelos en orden de preferencia: si uno esta saturado, probamos el siguiente
MODELS = ["gemini-3.6-flash", "gemini-3.8-flash", "gemini-4-argon", "gemini-3.5-flash"]
MAX_TRIES = 4  # intentos por modelo antes de pasar al siguiente
AUDIO_URL = "https://storage.googleapis.com/generativeai-downloads/data/State_of_the_Union_Address_30_January_1961.mp3"

# --- IMAGEN LOCAL ---
# "rb" = leer en modo binario (la imagen son bytes, no texto)
# La API recibe JSON, que solo admite texto, por eso convertimos los bytes a Base64
# b64encode devuelve bytes; .decode("utf-8") los convierte en un str
with open(ASSETS / "sample.jpg", "rb") as f:
    image_b64 = base64.b64encode(f.read()).decode("utf-8")

# --- AUDIO ---
# Mandar la URL directa dio error 400 ("invalid argument"); la causa exacta NO esta confirmada.
# Lo que si funciono: descargar el archivo y subirlo a la Files API de Google.
# Solo lo descargamos si todavia no existe, para no bajarlo en cada ejecucion
if not AUDIO_PATH.exists():
    urllib.request.urlretrieve(AUDIO_URL, AUDIO_PATH)

# files.upload devuelve un objeto con .uri, la referencia que usamos en la peticion
audio_file = client.files.upload(file=str(AUDIO_PATH), config={"mime_type": "audio/mp3"})


def ask(model):
    # interactions.create es la API NUEVA (Interactions). La clasica usa
    # models.generate_content(contents=...); aqui el parametro se llama "input"
    return client.interactions.create(
        model=model,
        input=[
            {"type": "text", "text": "Describe what you see in the image and summarize the audio."},
            # imagen: va dentro de la peticion, en Base64 ("data")
            {"type": "image", "data": image_b64, "mime_type": "image/jpeg"},
            # audio: va por referencia ("uri" del archivo ya subido)
            {"type": "audio", "uri": audio_file.uri, "mime_type": "audio/mp3"},
        ],
    )


for model in MODELS:
    for attempt in range(MAX_TRIES):
        try:
            interaction = ask(model)
            print(f"[{model}]")
            # output_text junta el texto de la respuesta (funciona en google-genai 3.2.0)
            print(interaction.output_text)
            raise SystemExit(0)  # exito: terminamos el programa
        except Exception as e:
            # El SDK 3.2.0 pone el codigo HTTP en e.status_code (no usa errors.ClientError)
            code = getattr(e, "status_code", None)
            # 429 (limite de uso) y 503 (servidor saturado) pasan solos con el tiempo.
            # Los demas 4xx (400, 404...) son culpa de la peticion: repetirla no arregla nada
            if code not in (429, 503):
                print(f"[{model}] error {code}: {str(e)[:200]} -> siguiente modelo")
                break
            # Backoff exponencial: espera 1s, 2s, 4s, 8s... (2 elevado al intento).
            # El random.random() (0 a 1 s) evita que muchos clientes reintenten a la vez
            wait = 2**attempt + random.random()
            print(f"[{model}] {code}, intento {attempt + 1}/{MAX_TRIES}, espero {wait:.1f}s")
            time.sleep(wait)
    else:
        # el else de un for solo corre si NO hubo break: se agotaron los intentos
        print(f"[{model}] sigue saturado, paso al siguiente modelo")

print("Ningun modelo respondio.")
