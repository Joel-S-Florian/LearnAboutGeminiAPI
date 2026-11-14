# 07.4b file_search: por que no recupera? Se prueba UNA variable a la vez:
#   A) con embedding_model=gemini-embedding-2 PERO con espera de 10 s tras indexar (aisla la espera)
# Se borra el store al final.

import time
from pathlib import Path

from google import genai

ASSETS = Path(__file__).resolve().parent.parent / "assets"
client = genai.Client(http_options={"timeout": 90_000})

store = client.file_search_stores.create(config={"display_name": "diag-notas", "embedding_model": "models/gemini-embedding-2"})
try:
    op = client.file_search_stores.upload_to_file_search_store(
        file=str(ASSETS / "sample_notas.txt"), file_search_store_name=store.name, config={"display_name": "notas"}
    )
    while not op.done:
        time.sleep(5)
        op = client.operations.get(op)
    time.sleep(10)  # margen por si el indice tarda en ser consultable (no verificado)
    r = client.interactions.create(
        model="gemini-3.5-flash-lite",
        input="Segun mis notas, cual es la palabra secreta del experimento de File Search?",
        tools=[{"type": "file_search", "file_search_store_names": [store.name]}],
    )
    print("pasos:", [s.type for s in r.steps])
    print(r.output_text)
finally:
    client.file_search_stores.delete(name=store.name, config={"force": True})
    print("store borrado")
