# 07.16 Code execution a fondo, parte 3: IMAGENES (doc: oficial en Gemini 3 Flash; el modelo puede hacer zoom, contar con codigo y anotar).
# Imagenes sinteticas con respuesta CONOCIDA (matplotlib, semilla fija):
#   1 detalle diminuto: un PIN de 4 digitos en la esquina de una imagen de 3000x2000      2 contar: 9 puntos verdes entre 23
#   3 anotar: dibujar un rectangulo alrededor del cuadrado azul y devolver la imagen
# Cada caso se hace SIN herramienta (linea base) y CON code_execution. Se muestra si el codigo del modelo toco la imagen (PIL/cv2/crop/resize),
# las respuestas frente a la verdad conocida, y se guardan las imagenes devueltas en salidas/ce_imagenes/ para VERLAS.
# Ejecutar con `python -u ... > archivo`.

import base64
import random
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from google import genai

SAL = Path(__file__).resolve().parent.parent / "salidas" / "ce_imagenes"
SAL.mkdir(parents=True, exist_ok=True)
client = genai.Client(http_options={"api_version": "v1beta", "timeout": 180_000})
MODELOS = ["gemini-3.5-flash-lite", "gemini-3.8-flash"]  # el segundo (20 peticiones/dia) solo si se pide con USAR_38=True
USAR_38 = False

# ---- imagen 1: PIN diminuto en una imagen grande
fig = plt.figure(figsize=(30, 20), dpi=100)
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 30); ax.set_ylim(0, 20); ax.axis("off")
ax.add_patch(plt.Rectangle((2, 3), 12, 12, color="#4477aa")); ax.add_patch(plt.Circle((22, 10), 5, color="#ee8866"))
ax.text(15, 18, "Panel de control", fontsize=60, ha="center")
ax.text(28.2, 0.4, "PIN 5824", fontsize=9, ha="right")
fig.savefig(SAL / "1_pin.png"); plt.close(fig)

# ---- imagen 2: puntos de colores (9 verdes, 8 rojos, 6 azules)
random.seed(3)
fig, ax = plt.subplots(figsize=(8, 8), dpi=100); ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off")
colores = ["green"] * 9 + ["red"] * 8 + ["blue"] * 6
random.shuffle(colores)
puntos = []
for col in colores:
    while True:
        x, y = random.uniform(0.5, 9.5), random.uniform(0.5, 9.5)
        if all((x - a) ** 2 + (y - b) ** 2 > 0.8 for a, b in puntos):
            puntos.append((x, y)); break
    ax.add_patch(plt.Circle((x, y), 0.22, color=col))
fig.savefig(SAL / "2_puntos.png"); plt.close(fig)

# ---- imagen 3: formas
fig, ax = plt.subplots(figsize=(6, 6), dpi=100); ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off")
ax.add_patch(plt.Rectangle((1, 6), 2.5, 2.5, color="red")); ax.add_patch(plt.Rectangle((6, 1.5), 2.5, 2.5, color="blue")); ax.add_patch(plt.Circle((3, 2.5), 1.2, color="green"))
fig.savefig(SAL / "3_formas.png"); plt.close(fig)


def b64(nombre):
    return base64.b64encode((SAL / nombre).read_bytes()).decode()


def preguntar(modelo, imagen, texto, con_codigo, etiqueta):
    contenido = [{"type": "image", "data": b64(imagen), "mime_type": "image/png"}, {"type": "text", "text": texto}]
    kw = {"tools": [{"type": "code_execution"}]} if con_codigo else {}
    try:
        r = client.interactions.create(model=modelo, input=contenido, **kw)
    except Exception as e:
        print(f"  [{etiqueta}] FALLO {type(e).__name__} {getattr(e, 'status_code', None)} {str(e)[:200]}")
        return
    codigo = " ".join(str(s.arguments.code) for s in r.steps if s.type == "code_execution_call")
    toca = [k for k in ("PIL", "cv2", "crop", "resize", "Image.open", "imread") if k in codigo]
    imgs = 0
    for s in r.steps:
        if s.type == "model_output":
            for b in s.content:
                if b.type == "image" and getattr(b, "data", None):
                    imgs += 1
                    f = SAL / f"salida_{etiqueta.replace(' ', '_').replace('/', '-')}_{imgs}.png"
                    f.write_bytes(base64.b64decode(b.data))
    print(f"  [{etiqueta}] tokens={getattr(r.usage, 'total_tokens', '?')} llamadas_codigo={codigo.count('def ') + (1 if codigo else 0) and sum(s.type == 'code_execution_call' for s in r.steps)} "
          f"| codigo toca la imagen: {toca} | imagenes devueltas: {imgs}\n      -> {(r.output_text or '')[:230]!r}")


for modelo in MODELOS if USAR_38 else MODELOS[:1]:
    print(f"\n########## modelo {modelo} ##########")
    print("\n--- 1 PIN diminuto (verdad: 5824) ---")
    Q1 = "There is a small PIN written somewhere in this image. What is it? Reply with the digits only."
    preguntar(modelo, "1_pin.png", Q1, False, "1 sin codigo")
    preguntar(modelo, "1_pin.png", Q1, True, "1 con codigo")
    print("\n--- 2 contar puntos verdes (verdad: 9 de 23) ---")
    Q2 = "How many green dots are in this image? Reply with the number only."
    preguntar(modelo, "2_puntos.png", Q2, False, "2 sin codigo")
    preguntar(modelo, "2_puntos.png", Q2, True, "2 con codigo")
    preguntar(modelo, "2_puntos.png", "Write code to count the green dots in this image. Reply with the number only.", True, "2 con codigo explicito")
    print("\n--- 3 anotar la imagen ---")
    preguntar(modelo, "3_formas.png", "Write code to draw a black rectangle outline around the blue square and return the annotated image.", True, "3 anotar")
