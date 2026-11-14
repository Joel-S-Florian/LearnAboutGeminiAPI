# 07.4 file_search: RAG sobre TUS archivos
# Flujo: crear un "store" -> subir el archivo (se parte en trozos, se embebe y se indexa)
# -> consultar con tools=[{"type": "file_search", ...}] -> el modelo responde con citas.
# Los archivos subidos a la Files API caducan en 48 h; lo importado al store queda hasta que
# se borre. Por eso este script borra el store al final (try/finally).

import time
from pathlib import Path

from google import genai

ASSETS = Path(__file__).resolve().parent.parent / "assets"

# Modelos con respaldo (la doc de File Search lista 3.x y 2.5 Pro/Flash-Lite, no 2.5 Flash)
MODELOS = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-2.5-flash-lite"]

client = genai.Client(http_options={"timeout": 90_000})

# El modelo de embeddings se elige al crear el store (gemini-embedding-2 admite texto e imagenes)
store = client.file_search_stores.create(
    config={
        "display_name": "notas-joel",
        "embedding_model": "models/gemini-embedding-2",
    }
)
print("Store creado:", store.name)

try:
    # Sube e importa en un paso. Devuelve una operacion larga: hay que esperar a que termine
    operation = client.file_search_stores.upload_to_file_search_store(
        file=str(ASSETS / "sample_notas.txt"),
        file_search_store_name=store.name,
        config={"display_name": "sample_notas"},
    )
    while not operation.done:
        time.sleep(5)
        operation = client.operations.get(operation)
    print("Indexado.")
    # Comprobar que el documento quedo en el store y en que estado
    for doc in client.file_search_stores.documents.list(parent=store.name):
        print("Documento:", doc.display_name, doc.state, doc.size_bytes)
    print()

    interaction = None
    for modelo in MODELOS:
        try:
            interaction = client.interactions.create(
                model=modelo,
                input="Segun mis notas, cual es la palabra secreta del experimento de File Search?",
                tools=[{"type": "file_search", "file_search_store_names": [store.name]}],
            )
            print(f"Modelo usado: {modelo}\n")
            break
        except Exception as e:
            print(f"[{modelo}] fallo: {type(e).__name__} {getattr(e, 'status_code', None)}")

    if interaction is None:
        raise SystemExit("Ningun modelo respondio.")

    print("Tipos de pasos:", [s.type for s in interaction.steps])
    for step in interaction.steps:
        # Depuracion: que devolvio cada busqueda en el store (vacio = no recupero nada)
        if step.type in ("file_search_call", "file_search_result"):
            print(f"[{step.type}]", str(step.model_dump(exclude={"signature"}))[:600])
        if step.type == "model_output":
            for bloque in step.content:
                if bloque.type == "text":
                    print(bloque.text)
                    # Citas de archivo: de que documento salio la respuesta
                    for a in bloque.annotations or []:
                        if a.type == "file_citation":
                            print(f" - fuente: {a.file_name}")
finally:
    # force=True borra el store aunque tenga documentos
    client.file_search_stores.delete(name=store.name, config={"force": True})
    print("\nStore borrado.")
