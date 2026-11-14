# 07.12 File Search a fondo, parte 5: MULTIMODAL (imagenes) y el embedding `gemini-embedding-2`.
# La doc usa `embedding_model: models/gemini-embedding-2` en TODOS sus ejemplos, y dice que es el embedding multimodal (el defecto,
# gemini-embedding-001, es solo de texto). En el tema anterior un store con embedding-2 NO recupero un archivo de TEXTO. Aqui:
#   A) mismo documento de texto en un store 001 (control) y en un store embedding-2; se pregunta tres veces (0, 30 y 60 s) por si es
#      cuestion de tiempo de indexado.   B) imagenes PNG (generadas con matplotlib) en el store embedding-2 y preguntas sobre ellas;
#   C) subir una imagen a un store 001 (que pasa?); D) media_id en la cita y client.file_search_stores.download_media().
# Las imagenes descargadas se guardan en salidas/fs_media/ para verlas. Se borran stores en finally.
# Ejecutar con `python -u ... > archivo`.

import tempfile
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from google import genai

RAIZ = Path(__file__).resolve().parent.parent
SALIDAS = RAIZ / "salidas" / "fs_media"
SALIDAS.mkdir(parents=True, exist_ok=True)
client = genai.Client(http_options={"timeout": 120_000})
S = client.file_search_stores
MODELO = "gemini-3.5-flash-lite"
tmp = Path(tempfile.mkdtemp())
stores = []

# imagenes sinteticas: una con un circulo rojo, otra con un triangulo verde y la palabra PINGUINO
fig, ax = plt.subplots(figsize=(4, 4)); ax.set_facecolor("#cfe3ff"); ax.add_patch(plt.Circle((0.5, 0.5), 0.3, color="red"))
ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off"); fig.savefig(tmp / "circulo.png", dpi=80); plt.close(fig)
fig, ax = plt.subplots(figsize=(4, 4)); ax.set_facecolor("#fff2b3"); ax.add_patch(plt.Polygon([[0.2, 0.2], [0.8, 0.2], [0.5, 0.75]], color="green"))
ax.text(0.5, 0.9, "PINGUINO", ha="center", fontsize=24); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off"); fig.savefig(tmp / "triangulo.png", dpi=80); plt.close(fig)


def esperar(op):
    while not op.done:
        time.sleep(4)
        op = client.operations.get(op)
    return op


def nuevo(nombre, embedding=None):
    cfg = {"display_name": nombre}
    if embedding:
        cfg["embedding_model"] = embedding
    s = S.create(config=cfg)
    stores.append(s.name)
    print(f"store '{nombre}': {s.name} | embedding_model = {S.get(name=s.name).embedding_model}")
    return s.name


def preguntar(store, pregunta):
    try:
        r = client.interactions.create(model=MODELO, input=pregunta, tools=[{"type": "file_search", "file_search_store_names": [store]}])
    except Exception as e:
        return f"RECHAZADO {getattr(e, 'status_code', None)} {str(e)[:200]}", []
    texto, anot = "", []
    for s in r.steps:
        if s.type == "model_output":
            for b in s.content:
                if b.type == "text":
                    texto += b.text
                    anot += [a.model_dump() for a in (b.annotations or [])]
    return texto.strip().replace("\n", " "), anot


try:
    print("=== A) el mismo TEXTO en 001 y en embedding-2 ===")
    T = nuevo("T2.5 texto 001")
    E = nuevo("T2.5 embedding-2", "models/gemini-embedding-2")
    for st in (T, E):
        esperar(S.upload_to_file_search_store(file=str(RAIZ / "assets" / "sample_notas.txt"), file_search_store_name=st, config={"display_name": "notas"}))
    Q = "Segun mis notas, cual es la palabra secreta del experimento de File Search? Cita tu fuente."
    for etiqueta, esperar_s in (("t=0", 0), ("t=+30s", 30), ("t=+60s", 30)):
        time.sleep(esperar_s)
        for nombre, st in (("001", T), ("embedding-2", E)):
            texto, anot = preguntar(st, Q)
            print(f"  [{etiqueta}] {nombre}: {'ENCONTRO mangu' if 'mangu' in texto.lower() else 'NO encontro'} | anotaciones={len(anot)} | {texto[:110]}")

    print("\n=== B) imagenes en el store embedding-2 ===")
    for f in ("circulo.png", "triangulo.png"):
        op = esperar(S.upload_to_file_search_store(file=str(tmp / f), file_search_store_name=E, config={"display_name": f.split(".")[0]}))
        print(f"  subida {f}: OK")
    docs = list(S.documents.list(parent=E))
    print("  documentos:", [(d.display_name, d.mime_type, d.size_bytes) for d in docs])
    time.sleep(10)
    for q in ("Which image shows a red circle? Name the image and cite it.",
              "What word is written in one of the images? Name the image and cite it."):
        texto, anot = preguntar(E, q)
        print(f"\n  P: {q}\n  R: {texto[:230]}\n  anotaciones={len(anot)}")
        for a in anot:
            print("   -", {k: (v[:90] if isinstance(v, str) else v) for k, v in a.items() if v is not None})
            if a.get("media_id"):
                try:
                    data = client.file_search_stores.download_media(media_id=a["media_id"])
                    destino = SALIDAS / f"{a.get('file_name', 'media')}_{abs(hash(a['media_id'])) % 10000}.png"
                    destino.write_bytes(data)
                    print(f"     download_media -> {len(data)} bytes guardados en {destino.name} (cabecera PNG: {data[:4] == bytes([137, 80, 78, 71])})")
                except Exception as e:
                    print("     download_media fallo:", getattr(e, "status_code", None), str(e)[:160])

    print("\n=== C) imagen en un store 001 (solo texto) ===")
    try:
        op = esperar(S.upload_to_file_search_store(file=str(tmp / "circulo.png"), file_search_store_name=T, config={"display_name": "circulo"}))
        err = getattr(op, "error", None)
        print("  subida aceptada; error de la operacion:", str(err)[:200] if err else "ninguno")
        print("  documentos del store 001:", [(d.display_name, d.mime_type, str(d.state)) for d in S.documents.list(parent=T)])
    except Exception as e:
        print("  RECHAZADA:", getattr(e, "status_code", None), str(e)[:250])
finally:
    for n in stores:
        try:
            S.delete(name=n, config={"force": True})
        except Exception:
            pass
    print("\nstores que quedan:", [s.name for s in S.list()])
