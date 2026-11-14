# 07.11 File Search a fondo, parte 4: CITAS con NUMERO DE PAGINA en un PDF. Se genera con matplotlib un PDF de 6 paginas (texto
# real, fuente TrueType incrustada: pdf.fonttype=42, para que sea extraible) donde cada pagina tiene una palabra secreta distinta.
# Se indexa (por subida directa) y se pregunta por datos de paginas concretas, con y sin pedir la cita en el prompt; se compara
# `annotation.page_number` con la pagina REAL donde esta el dato. Se borra el store en finally. Ejecutar con `python -u ... > archivo`.

import tempfile
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

from google import genai

plt.rcParams["pdf.fonttype"] = 42  # texto seleccionable (con el valor por defecto, 3, algunos lectores no extraen el texto)
client = genai.Client(http_options={"timeout": 90_000})
S = client.file_search_stores
MODELO = "gemini-3.5-flash-lite"
SECRETOS = {1: "fresa", 2: "lavanda", 3: "obsidiana", 4: "girasol", 5: "cuarzo", 6: "menta"}

ruta = Path(tempfile.mkdtemp()) / "informe.pdf"
with PdfPages(ruta) as pdf:
    for n, sec in SECRETOS.items():
        fig = plt.figure(figsize=(8.27, 11.69))
        fig.text(0.1, 0.9, f"Informe del laboratorio - Pagina {n}", fontsize=18)
        fig.text(0.1, 0.8, f"Seccion {n}. El numero de registro de la pagina {n} es {n}00.", fontsize=12)
        fig.text(0.1, 0.75, f"La palabra secreta de la pagina {n} es: {sec}.", fontsize=12)
        fig.text(0.1, 0.7, "Este parrafo es de relleno y no contiene datos utiles para las preguntas.", fontsize=10)
        pdf.savefig(fig)
        plt.close(fig)
print(f"PDF generado: {ruta.stat().st_size} bytes, {len(SECRETOS)} paginas")

store = None


def esperar(op):
    while not op.done:
        time.sleep(4)
        op = client.operations.get(op)
    return op


def preguntar(pregunta):
    r = client.interactions.create(model=MODELO, input=pregunta, tools=[{"type": "file_search", "file_search_store_names": [store]}])
    texto, anot = "", []
    for s in r.steps:
        if s.type == "model_output":
            for b in s.content:
                if b.type == "text":
                    texto += b.text
                    anot += [a.model_dump() for a in (b.annotations or [])]
    return texto.strip().replace("\n", " "), anot


try:
    store = S.create(config={"display_name": "T2.4 pdf"}).name
    esperar(S.upload_to_file_search_store(file=str(ruta), file_search_store_name=store, config={"display_name": "informe"}))
    d = list(S.documents.list(parent=store))[0]
    print("documento:", d.display_name, d.mime_type, d.size_bytes, "bytes,", d.state)

    PREGUNTAS = [
        ("pagina 3, sin pedir cita", "Que palabra secreta aparece en la pagina 3 del informe?"),
        ("pagina 3, pidiendo cita", "Que palabra secreta aparece en la pagina 3 del informe? Cita tu fuente."),
        ("dato sin decir la pagina", "Cual es el numero de registro 500? Dime la palabra secreta de esa pagina. Cita tu fuente."),
        ("paginas 2 y 6", "Dame las palabras secretas de las paginas 2 y 6 del informe. Cita tus fuentes."),
    ]
    for nombre, p in PREGUNTAS:
        texto, anot = preguntar(p)
        print(f"\n[{nombre}]\n   respuesta: {texto[:200]}\n   anotaciones: {len(anot)}")
        for a in anot:
            sec = next((s for n, s in SECRETOS.items() if s in a.get("source", "")), None)
            pag_real = next((n for n, s in SECRETOS.items() if s == sec), None)
            print(f"   - page_number={a.get('page_number')} | secreto en el chunk={sec} (pagina real={pag_real}) | "
                  f"claves={sorted(k for k, v in a.items() if v is not None and k != 'source')} | source[:70]={a.get('source', '')[:70]!r}")
finally:
    if store:
        S.delete(name=store, config={"force": True})
    print("\nstores que quedan:", [s.name for s in S.list()])
