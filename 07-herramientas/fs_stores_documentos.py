# 07.8 File Search a fondo, parte 1: la API de STORES y DOCUMENTOS (sin llamar al modelo: todo gratis).
# Se prueba: crear (display_name vs name, nombre fijo), listar con paginacion, get, subir documentos y gestionarlos
# (documents.list/get/delete), borrar un store con y sin force, y los errores. Todo lo creado se borra en finally.
# Ejecutar con `python -u ... > archivo`.

import tempfile
import time
from pathlib import Path

from google import genai

client = genai.Client(http_options={"timeout": 90_000})
S = client.file_search_stores
creados = []


def intento(titulo, fn):
    try:
        r = fn()
        print(f"[{titulo}] OK")
        return r
    except Exception as e:
        print(f"[{titulo}] fallo: {getattr(e, 'status_code', None)} {str(e)[:210]}")


def campos(o):
    d = o.model_dump() if hasattr(o, "model_dump") else dict(o)
    return {k: v for k, v in d.items() if v is not None}


def esperar(op):
    while not op.done:
        time.sleep(4)
        op = client.operations.get(op)
    return op


print("stores ya existentes antes de empezar:", [s.name for s in S.list()])
tmp = Path(tempfile.mkdtemp())
(tmp / "uno.txt").write_text("Documento uno. La palabra clave del uno es: aguacate.", encoding="utf-8")
(tmp / "dos.md").write_text("# Documento dos\nLa palabra clave del dos es: tamarindo.", encoding="utf-8")

try:
    # 1) crear: nombre autogenerado y nombre fijo
    a = S.create(config={"display_name": "Estudio Store A"})
    creados.append(a.name)
    print("\n1) store A:", campos(a))
    b = intento("crear con name fijo", lambda: S.create(config={"name": "estudio-fijo-1", "display_name": "Estudio B"}))
    if b:
        creados.append(b.name)
        print("   store B:", campos(b))
    intento("crear OTRA VEZ con el mismo name fijo", lambda: S.create(config={"name": "estudio-fijo-1", "display_name": "Estudio B2"}))
    c = intento("crear con el mismo display_name que A", lambda: S.create(config={"display_name": "Estudio Store A"}))
    if c:
        creados.append(c.name)
        print("   nombres de A y C distintos:", a.name != c.name)

    # 2) get y list con paginacion
    print("\n2) get A:", campos(S.get(name=a.name)))
    pag = S.list(config={"page_size": 2})
    print("   list(page_size=2): primera pagina tiene", len(list(pag.page)) if hasattr(pag, "page") else "?", "elementos")
    print("   todos los stores:", [s.name for s in S.list()])
    intento("get de un store inexistente", lambda: S.get(name="fileSearchStores/no-existe-xyz"))

    # 3) subir documentos y gestionarlos
    for f, nombre in (("uno.txt", "Doc Uno"), ("dos.md", "Doc Dos")):
        op = esperar(S.upload_to_file_search_store(file=str(tmp / f), file_search_store_name=a.name, config={"display_name": nombre}))
        print(f"\n3) subido {f}: operacion done={op.done}", "| response:", str(getattr(op, "response", None))[:200])
    docs = list(S.documents.list(parent=a.name))
    print("   documents.list:", [(d.name.split("/")[-1], d.display_name, str(d.state), d.size_bytes, d.mime_type) for d in docs])
    print("   documents.get:", campos(S.documents.get(name=docs[0].name)))
    print("   get del store A tras subir:", campos(S.get(name=a.name)))
    intento("borrar un documento", lambda: S.documents.delete(name=docs[0].name, config={"force": True}))
    print("   documentos que quedan:", [d.display_name for d in S.documents.list(parent=a.name)])
    intento("get del documento borrado", lambda: S.documents.get(name=docs[0].name))

    # 4) borrar un store con documentos SIN force y CON force
    intento("delete SIN force (el store tiene documentos)", lambda: S.delete(name=a.name))
    intento("delete CON force", lambda: S.delete(name=a.name, config={"force": True}))
    if a.name in creados:
        creados.remove(a.name)
    intento("delete del mismo store otra vez", lambda: S.delete(name=a.name, config={"force": True}))
finally:
    for n in creados:
        try:
            S.delete(name=n, config={"force": True})
        except Exception:
            pass
    print("\nstores que quedan:", [s.name for s in S.list()])
