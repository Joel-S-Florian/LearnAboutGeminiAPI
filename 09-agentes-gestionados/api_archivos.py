# 09.20 API de archivos del entorno: client.environments.files.list / download / upload.
# Todo es gratis (no usa al agente): se crea un entorno vacio con environments.create() y se borra al final.
# Se prueba: subir un archivo (y el 409 al repetir sin overwrite), subir y EXTRAER un tar.gz, listar (raiz,
# subcarpeta, recursivo), metadatos de un archivo, descargar archivo y carpeta (tar), 404, y subir un binario.

import io
import tarfile

from google import genai

client = genai.Client(http_options={"api_version": "v1beta", "timeout": 120_000})
F = client.environments.files


def intento(titulo, fn):
    try:
        r = fn()
        print(f"[{titulo}] OK")
        return r
    except Exception as e:
        print(f"[{titulo}] fallo: {getattr(e, 'status_code', None)} {str(e)[:150]}")


def nombres(resp):
    return [(f.path, f.type, getattr(f, "size_bytes", None)) for f in (resp.files or [])]


env = client.environments.create().id
try:
    sube = lambda path, data, **kw: F.upload(environment=env, path=path, file=io.BytesIO(data), **kw)

    # 1) subir un archivo; las carpetas padre se crean solas
    r = intento("subir 1 archivo", lambda: sube("workspace/data/hola.txt", b"hola mundo", mime_type="text/plain"))
    if r: print("   ->", nombres(r))
    # 2) repetir sin overwrite -> 409 segun la doc
    intento("subir otra vez SIN overwrite", lambda: sube("workspace/data/hola.txt", b"v2", mime_type="text/plain"))
    # 3) con overwrite=True
    intento("subir otra vez CON overwrite", lambda: sube("workspace/data/hola.txt", b"v2", mime_type="text/plain", overwrite=True))

    # 4) tar.gz en memoria y extraerlo
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as t:
        for n, c in {"app.py": b"print('hi')\n", "requirements.txt": b"requests\n"}.items():
            ti = tarfile.TarInfo(n); ti.size = len(c); t.addfile(ti, io.BytesIO(c))
    r = intento("subir y extraer tar.gz", lambda: sube("workspace/src/", buf.getvalue(), extract=True))
    if r: print("   ->", [p for p, _, _ in nombres(r)])
    intento("extraer de nuevo SIN overwrite", lambda: sube("workspace/src/", buf.getvalue(), extract=True))

    # 5) listar
    print("\nraiz        :", nombres(F.list(environment=env, path="")))
    print("workspace   :", nombres(F.list(environment=env, path="workspace")))
    print("recursivo   :", [p for p, _, _ in nombres(F.list(environment=env, path="workspace", recursive=True))])
    print("metadatos   :", nombres(F.list(environment=env, path="workspace/data/hola.txt")))
    intento("listar ruta inexistente", lambda: F.list(environment=env, path="no/existe.txt"))

    # 6) descargar archivo y carpeta
    c = F.download(environment=env, path="workspace/data/hola.txt")
    print("\ndescarga archivo:", type(c).__name__, c)
    d = F.download(environment=env, path="workspace/src")
    with tarfile.open(fileobj=io.BytesIO(d)) as t:
        print("descarga carpeta (tar):", t.getnames())

    # 7) binario (la doc dice que el AGENTE solo lee texto e imagenes; subirlo es otra cosa)
    r = intento("subir binario", lambda: sube("workspace/data/datos.bin", bytes(range(256)), mime_type="application/octet-stream"))
    if r: print("   ->", nombres(r))
finally:
    client.environments.delete(id=env)
    print("\nentorno borrado; quedan:", [x.id[:8] for x in client.environments.list().environments or []])
