# 09.2b Descargar el entorno (sandbox) de un agente: baja una "foto" (.tar) de todos sus archivos.
# No hay metodo del SDK todavia: es una peticion HTTP directa a la Files API con tu clave en la cabecera.
# Uso:  python descargar_entorno.py <environment_id>
# Deja el .tar y lo extraido en salidas/ (ignorada por git). Se pone un tope de tamano por prudencia.

import os
import sys
import tarfile
from pathlib import Path

import requests

SALIDAS = Path(__file__).resolve().parent.parent / "salidas"
SALIDAS.mkdir(exist_ok=True)
TOPE_MB = 200

if len(sys.argv) != 2:
    raise SystemExit("Uso: python descargar_entorno.py <environment_id>")
env_id = sys.argv[1]

destino = SALIDAS / f"entorno_{env_id[:8]}.tar"
if destino.exists():  # no volver a bajar ~100 MB si ya esta
    print(f"Ya existe {destino.name}, se reutiliza")
else:
    url = f"https://generativelanguage.googleapis.com/v1beta/files/environment-{env_id}:download"
    respuesta = requests.get(
        url,
        params={"alt": "media"},
        headers={"x-goog-api-key": os.environ["GEMINI_API_KEY"]},  # la clave sale del entorno, no del codigo
        allow_redirects=True,
        stream=True,
        timeout=120,
    )
    respuesta.raise_for_status()
    total = 0
    with open(destino, "wb") as f:
        for trozo in respuesta.iter_content(1 << 20):
            total += len(trozo)
            if total > TOPE_MB * 1024 * 1024:
                raise SystemExit(f"Mas de {TOPE_MB} MB: abortado (revisa antes de bajar todo)")
            f.write(trozo)
    print(f"Descargado: {destino.name} ({total / 1024:.1f} KB)")

# OJO: la "foto" es el sistema de archivos ENTERO del sandbox (~95 MB, con paquetes de Python, /usr, etc.).
# Extraerlo todo fallo: filter="data" rechaza archivos especiales del sistema. Solo extraemos los archivos
# de TRABAJO (imagenes, texto, csv, py) que esten en la raiz o en /workspace.
EXTENSIONES = {".png", ".jpg", ".txt", ".csv", ".md", ".py", ".pdf", ".json"}
carpeta = SALIDAS / f"entorno_{env_id[:8]}"
with tarfile.open(destino) as tar:
    elegidos = []
    for m in tar.getmembers():
        partes = Path(m.name).parts  # p. ej. ('.', 'chart.png') o ('.', 'workspace', 'x.txt')
        partes = [p for p in partes if p != "."]
        en_trabajo = len(partes) == 1 or (len(partes) == 2 and partes[0] == "workspace")
        if m.isfile() and en_trabajo and Path(m.name).suffix.lower() in EXTENSIONES:
            elegidos.append(m)
    print(f"Miembros en el .tar: {len(tar.getmembers())} | archivos de trabajo elegidos: {len(elegidos)}")
    # filter="data": rechaza rutas peligrosas (absolutas, "..", enlaces fuera de la carpeta)
    tar.extractall(path=carpeta, members=elegidos, filter="data")
print(f"Extraido en: {carpeta}")
for m in elegidos:
    print(" -", m.name, f"({m.size} bytes)")
