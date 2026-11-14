# 07.15 Code execution a fondo, parte 2: ARCHIVOS DE ENTRADA y GRAFICOS DE SALIDA. La doc: la entrada puede ir inline o por la Files API,
# la salida (graficos de matplotlib) siempre vuelve inline como imagen. Se genera un CSV de 240 filas con semilla fija, se calculan LOCALMENTE
# (pandas) las respuestas correctas y se compara con lo que dice el modelo. Tres formas de dar el archivo:
#   A) bloque `document` con datos en Base64 (inline)   B) bloque `document` con la URI de la Files API   C) el CSV pegado como texto
# Los graficos devueltos se guardan en salidas/ce_graficos/ para VERLOS. Se borra el archivo de la Files API en finally.
# Ejecutar con `python -u ... > archivo`.

import base64
import random
from pathlib import Path

import pandas as pd

from google import genai

RAIZ = Path(__file__).resolve().parent.parent
SAL = RAIZ / "salidas" / "ce_graficos"
SAL.mkdir(parents=True, exist_ok=True)
client = genai.Client(http_options={"api_version": "v1beta", "timeout": 180_000})
MODELO = "gemini-3.5-flash-lite"

# CSV determinista
random.seed(7)
filas = []
for i in range(240):
    mes = 1 + i % 12
    filas.append({"fecha": f"2026-{mes:02d}-{1 + i % 28:02d}", "region": random.choice(["norte", "sur", "este", "oeste"]),
                  "producto": random.choice(["cafe", "te", "cacao"]), "unidades": random.randint(1, 20), "precio": random.choice([2.5, 3.0, 4.75])})
df = pd.DataFrame(filas)
ruta = SAL / "ventas_240.csv"
df.to_csv(ruta, index=False)
df["ingreso"] = df.unidades * df.precio
ESPERADO_NORTE = round(df[df.region == "norte"].ingreso.sum(), 2)
ESPERADO_PRODUCTO = df.groupby("producto").unidades.sum().idxmax()
print(f"CSV: {len(df)} filas, {ruta.stat().st_size} bytes | ESPERADO (pandas): ingreso de 'norte' = {ESPERADO_NORTE}, producto con mas unidades = {ESPERADO_PRODUCTO}")

PROMPT = ("Using the CSV data, with code execution: (1) compute the total revenue (unidades * precio) of region 'norte' and give it with 2 decimals; "
          "(2) tell me which producto has the most total unidades; (3) draw a bar chart of monthly revenue with matplotlib. Be concise.")


def correr(titulo, contenido):
    print(f"\n===== {titulo} =====")
    try:
        r = client.interactions.create(model=MODELO, input=contenido, tools=[{"type": "code_execution"}])
    except Exception as e:
        print(f"  FALLO: {type(e).__name__} {getattr(e, 'status_code', None)} {str(e)[:300]}")
        return
    print(f"  estado={r.status} tokens={getattr(r.usage, 'total_tokens', '?')} pasos={[s.type for s in r.steps]}")
    imgs, tipos = 0, set()
    for s in r.steps:
        if s.type == "model_output":
            for b in s.content:
                tipos.add(b.type)
                if b.type == "image" and getattr(b, "data", None):
                    imgs += 1
                    f = SAL / f"{titulo[:1]}_{imgs}.png"
                    f.write_bytes(base64.b64decode(b.data))
                    print(f"  imagen devuelta -> {f.name} ({f.stat().st_size} bytes, mime={getattr(b, 'mime_type', None)})")
        elif s.type == "code_execution_result":
            tipos.add("result:" + type(s.result).__name__)
    print(f"  tipos de contenido vistos: {sorted(tipos)} | imagenes: {imgs}")
    texto = (r.output_text or "").replace("\n", " ")
    print(f"  texto: {texto[:420]}")
    print(f"  ¿menciona {ESPERADO_NORTE}? {str(ESPERADO_NORTE) in texto.replace(',', '')} | ¿menciona '{ESPERADO_PRODUCTO}'? {ESPERADO_PRODUCTO in texto.lower()}")


archivo_api = None
try:
    datos = base64.b64encode(ruta.read_bytes()).decode()
    correr("A inline base64", [{"type": "document", "data": datos, "mime_type": "text/csv"}, {"type": "text", "text": PROMPT}])
    archivo_api = client.files.upload(file=str(ruta), config={"display_name": "ventas_240", "mime_type": "text/csv"})
    print(f"\nFiles API: {archivo_api.name} state={archivo_api.state}")
    correr("B Files API (uri)", [{"type": "document", "uri": archivo_api.uri, "mime_type": "text/csv"}, {"type": "text", "text": PROMPT}])
    correr("C CSV como texto", [{"type": "text", "text": "CSV data:\n" + ruta.read_text(encoding="utf-8")}, {"type": "text", "text": PROMPT}])
finally:
    if archivo_api:
        client.files.delete(name=archivo_api.name)
        print("\narchivo de la Files API borrado")
