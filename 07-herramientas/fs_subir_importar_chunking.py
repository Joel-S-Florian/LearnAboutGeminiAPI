# 07.9 File Search a fondo, parte 2: SUBIR directo vs IMPORTAR desde la Files API, y chunking_config.
# Un documento con 12 "equipos" (cada uno con una mascota distinta) se indexa en TRES stores (embedding por defecto = 001):
#   A) subida directa (upload_to_file_search_store)       B) Files API + import_file       C) subida directa con chunking pequeno
# Se hacen dos preguntas a cada store (un dato suelto y tres datos repartidos) y se mira la respuesta y las anotaciones de cita.
# Tambien se prueban valores raros de chunking_config y que pasa con el File de la Files API (se borra al final).
# Todo (stores y archivo) se borra en finally. Ejecutar con `python -u ... > archivo`.

import tempfile
import time
from pathlib import Path

from google import genai

client = genai.Client(http_options={"timeout": 90_000})
S = client.file_search_stores
MODELO = "gemini-3.5-flash-lite"
stores, archivos = [], []

MASCOTAS = ["tucan", "jaguar", "delfin", "colibri", "armadillo", "manati", "ocelote", "pelicano", "iguana", "capibara", "zorzal", "tortuga"]
parrafos = []
for n, m in enumerate(MASCOTAS, 1):
    parrafos.append(
        f"Equipo {n}. El equipo numero {n} del torneo regional entrena los martes y jueves en el polideportivo {n} de la ciudad, "
        f"donde su entrenador {n} prepara jugadas sencillas para los partidos del fin de semana. Su mascota oficial es el {m}. "
        f"Los aficionados del equipo {n} suelen llevar bufandas de colores y cantar canciones sobre su mascota durante todo el partido.")
TEXTO = "\n\n".join(parrafos)
ruta = Path(tempfile.mkdtemp()) / "torneo.txt"
ruta.write_text(TEXTO, encoding="utf-8")
print(f"documento: {len(TEXTO)} caracteres, {len(parrafos)} parrafos")


def esperar(op):
    while not op.done:
        time.sleep(4)
        op = client.operations.get(op)
    return op


def nuevo_store(nombre):
    s = S.create(config={"display_name": nombre})
    stores.append(s.name)
    return s.name


def preguntar(store, pregunta):
    r = client.interactions.create(model=MODELO, input=pregunta, tools=[{"type": "file_search", "file_search_store_names": [store]}])
    texto, anot = "", []
    for s in r.steps:
        if s.type == "model_output":
            for b in s.content:
                if b.type == "text":
                    texto += b.text
                    anot += [a.model_dump() for a in (b.annotations or [])]
    return r, texto.strip().replace("\n", " "), anot


try:
    # A) subida directa
    A = nuevo_store("T2.2 A directa")
    esperar(S.upload_to_file_search_store(file=str(ruta), file_search_store_name=A, config={"display_name": "torneo"}))
    # B) Files API + import
    B = nuevo_store("T2.2 B importada")
    f = client.files.upload(file=str(ruta), config={"display_name": "torneo-import"})
    archivos.append(f.name)
    print("\nFiles API: name =", f.name, "| state =", f.state, "| expira:", getattr(f, "expiration_time", None))
    esperar(S.import_file(file_search_store_name=B, file_name=f.name))
    print("el File sigue en la Files API tras importar:", f.name in [x.name for x in client.files.list()])
    # C) chunking pequeno
    C = nuevo_store("T2.2 C chunk 40")
    esperar(S.upload_to_file_search_store(file=str(ruta), file_search_store_name=C, config={
        "display_name": "torneo", "chunking_config": {"white_space_config": {"max_tokens_per_chunk": 40, "max_overlap_tokens": 5}}}))
    for nombre, st in (("A directa", A), ("B importada", B), ("C chunk 40", C)):
        print(f"{nombre}: {S.get(name=st).size_bytes} bytes, {S.get(name=st).active_documents_count} doc")

    P1 = "Segun el documento del torneo, cual es la mascota del equipo 7?"
    P2 = "Segun el documento del torneo, dime la mascota de los equipos 2, 5 y 9."
    for nombre, st in (("A directa", A), ("B importada", B), ("C chunk 40", C)):
        for p in (P1, P2):
            r, texto, anot = preguntar(st, p)
            print(f"\n[{nombre}] {p[-34:]} -> {texto[:230]}")
            print(f"   pasos={[s.type for s in r.steps]} anotaciones={len(anot)} tokens={getattr(r.usage, 'total_tokens', '?')}")
            if anot:
                print("   anotacion[0]:", {k: v for k, v in anot[0].items() if v is not None})

    # chunking_config con valores raros (se prueba solo si la API lo rechaza al llamar o al terminar la operacion)
    print("\n--- valores raros de chunking_config ---")
    for max_t, ov in ((10, 20), (1, 0), (100000, 0), (0, 0)):
        try:
            op = S.upload_to_file_search_store(file=str(ruta), file_search_store_name=C, config={
                "display_name": f"raro-{max_t}-{ov}", "chunking_config": {"white_space_config": {"max_tokens_per_chunk": max_t, "max_overlap_tokens": ov}}})
            op = esperar(op)
            err = getattr(op, "error", None)
            print(f"max={max_t} overlap={ov}: operacion terminada, error={str(err)[:160] if err else 'ninguno'}")
        except Exception as e:
            print(f"max={max_t} overlap={ov}: RECHAZADO {getattr(e, 'status_code', None)} {str(e)[:200]}")
finally:
    for n in stores:
        try:
            S.delete(name=n, config={"force": True})
        except Exception:
            pass
    for n in archivos:
        try:
            client.files.delete(name=n)
        except Exception:
            pass
    print("\nstores que quedan:", [s.name for s in S.list()], "| archivos de la Files API:", [x.name for x in client.files.list()])
