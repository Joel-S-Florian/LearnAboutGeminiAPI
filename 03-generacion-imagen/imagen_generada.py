# 6. Multimodal generation
# Gemini puede GENERAR imagenes de forma nativa con los modelos "Nano Banana".
# En el tema 5 la imagen era ENTRADA (la mandabamos); aqui es SALIDA (la recibimos).

import base64

from pathlib import Path

from google import genai

# Carpeta de salidas junto a la raiz del repo (ignorada por git)
SALIDAS = Path(__file__).resolve().parent.parent / "salidas"
SALIDAS.mkdir(exist_ok=True)

# Igual que antes: el SDK busca la variable de entorno GEMINI_API_KEY
client = genai.Client()

# Misma API nueva (interactions.create). Aqui "input" es un str simple porque
# solo mandamos texto; en el tema 5 era una lista porque mezclabamos formatos
interaction = client.interactions.create(
    model="gemini-3.1-flash-image",
    input="Generate an image of a futuristic city skyline at sunset",
)

# La imagen vuelve en Base64 (texto), igual que cuando la mandamos, pero al reves.
# La respuesta la guarda en un "step" dentro de interaction.steps;
# output_image es un atajo que devuelve el ultimo bloque de imagen generado
imagen = interaction.output_image
if imagen is None:
    # Si el modelo no genero imagen (p. ej. la rechazo por seguridad), mostramos su texto
    print("No se genero imagen. Respuesta del modelo:")
    print(interaction.output_text)
else:
    # b64decode: Base64 (str) -> bytes. "wb" = escribir en modo binario
    with open(SALIDAS / "generated_image.png", "wb") as f:
        f.write(base64.b64decode(imagen.data))
    print("Imagen guardada en salidas/generated_image.png")
