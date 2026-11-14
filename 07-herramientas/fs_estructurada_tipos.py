# 07.13 File Search a fondo, parte 6: SALIDA ESTRUCTURADA, combinar con otras herramientas, y TIPOS DE ARCHIVO.
# La lista de tipos soportados NO vino en la doc pegada ("listed in the following sections"), asi que se prueba con archivos reales.
#   A) response_format JSON + file_search (doc: desde Gemini 3) con un CSV; y con 2.5 (se espera 400 como en tool+JSON anteriores)
#   B) file_search + url_context / google_search (la pagina de File Search dice que NO se combina)
#   C) tipos: .txt .md .csv .json .html .py .xml .log, sin extension, extension rara, vacio, audio WAV (la doc dice que no se soporta)
# Embedding por defecto (001) y preguntas en espanol. Se borra el store en finally. Ejecutar con `python -u ... > archivo`.
# NO se prueba el limite de 100 MB: subir un archivo grande y aceptado costaria embeddings de indexado.

import json
import tempfile
import time
import wave
from pathlib import Path

from google import genai
from pydantic import BaseModel, Field

RAIZ = Path(__file__).resolve().parent.parent
client = genai.Client(http_options={"api_version": "v1beta", "timeout": 120_000})
S = client.file_search_stores
MODELO = "gemini-3.5-flash-lite"
tmp = Path(tempfile.mkdtemp())
stores = []


def esperar(op):
    while not op.done:
        time.sleep(4)
        op = client.operations.get(op)
    return op


def nuevo(nombre):
    s = S.create(config={"display_name": nombre}).name
    stores.append(s)
    return s


def llamar(modelo, store, pregunta, extra_tools=(), **kw):
    try:
        r = client.interactions.create(model=modelo, input=pregunta, tools=[{"type": "file_search", "file_search_store_names": [store]}, *extra_tools], **kw)
    except Exception as e:
        return None, f"RECHAZADO {getattr(e, 'status_code', None)} {str(e)[:240]}"
    return r, r.output_text or ""


class Ventas(BaseModel):
    mejor_mes: str = Field(description="The month with the highest sales")
    ventas: int = Field(description="Sales of that month")
    total_trimestre: int = Field(description="Total sales of the three months")


try:
    # ---- A) estructurada
    print("=== A) salida estructurada + file_search ===")
    A = nuevo("T2.6 csv")
    esperar(S.upload_to_file_search_store(file=str(RAIZ / "assets" / "ventas_q3.csv"), file_search_store_name=A, config={"display_name": "ventas"}))
    FMT = {"type": "text", "mime_type": "application/json", "schema": Ventas.model_json_schema()}
    for modelo in ("gemini-3.5-flash-lite", "gemini-2.5-flash-lite"):
        r, t = llamar(modelo, A, "Using the sales file, which month had the highest sales, how much, and what was the total of the quarter?", response_format=FMT)
        if r is None:
            print(f"  [{modelo}] {t}")
            continue
        try:
            v = Ventas.model_validate_json(t)
            print(f"  [{modelo}] JSON valido: {v} | pasos={[s.type for s in r.steps]}")
        except Exception as e:
            print(f"  [{modelo}] NO valida: {type(e).__name__} | texto={t[:160]!r}")
        anot = [a for s in r.steps if s.type == "model_output" for b in s.content if b.type == "text" for a in (b.annotations or [])]
        print(f"     anotaciones de cita en modo JSON: {len(anot)}")

    # ---- B) combinar
    print("\n=== B) file_search + otras herramientas integradas ===")
    for etiqueta, tool, modelo in (("url_context", {"type": "url_context"}, MODELO), ("google_search (3.x)", {"type": "google_search"}, MODELO),
                                   ("google_search (2.5)", {"type": "google_search"}, "gemini-2.5-flash-lite")):
        r, t = llamar(modelo, A, "From the sales file, what were the sales of agosto?", extra_tools=[tool])
        print(f"  file_search + {etiqueta}: " + (t[:200].replace("\n", " ") if r else t) + (f" | pasos={sorted({s.type for s in r.steps})}" if r else ""))

    # ---- C) tipos de archivo
    print("\n=== C) tipos de archivo ===")
    C = nuevo("T2.6 tipos")
    contenidos = {
        "a.txt": "Texto plano. La palabra secreta es: nectarina.", "b.md": "# Titulo\nLa palabra secreta es: papaya.",
        "c.csv": "clave,valor\npalabra_secreta,guayaba", "d.json": json.dumps({"palabra_secreta": "maracuya"}),
        "e.html": "<html><body><p>La palabra secreta es: tamarindo.</p></body></html>", "f.py": "# La palabra secreta es: carambola\nprint('hola')",
        "g.xml": "<root><secreto>chirimoya</secreto></root>", "h.log": "2026-11-14 INFO La palabra secreta es: pitahaya",
        "sin_extension": "La palabra secreta es: litchi.", "raro.xyz": "La palabra secreta es: rambutan.", "vacio.txt": "",
    }
    for nombre, texto in contenidos.items():
        (tmp / nombre).write_text(texto, encoding="utf-8")
    with wave.open(str(tmp / "silencio.wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(16000); w.writeframes(bytes(32000))
    for nombre in sorted(p.name for p in tmp.iterdir()):
        try:
            op = esperar(S.upload_to_file_search_store(file=str(tmp / nombre), file_search_store_name=C, config={"display_name": nombre}))
            err = getattr(op, "error", None)
            print(f"  {nombre:14} subida aceptada" + (f" | error de la operacion: {str(err)[:120]}" if err else ""))
        except Exception as e:
            print(f"  {nombre:14} RECHAZADA {getattr(e, 'status_code', None)} {str(e)[:170]}")
    docs = list(S.documents.list(parent=C))
    print("\n  documentos que quedaron:", [(d.display_name, d.mime_type, str(d.state).split('.')[-1], d.size_bytes) for d in docs])
    time.sleep(10)
    r, t = llamar(MODELO, C, "Search all documents and list every secret word you find, separated by commas. Reply only with the words.")
    esperadas = ["nectarina", "papaya", "guayaba", "maracuya", "tamarindo", "carambola", "chirimoya", "pitahaya", "litchi", "rambutan"]
    print("  respuesta:", (t or "")[:300].replace("\n", " "))
    print("  recuperadas:", [w for w in esperadas if w in t.lower()], "| NO recuperadas:", [w for w in esperadas if w not in t.lower()])
finally:
    for n in stores:
        try:
            S.delete(name=n, config={"force": True})
        except Exception:
            pass
    print("\nstores que quedan:", [s.name for s in S.list()])
