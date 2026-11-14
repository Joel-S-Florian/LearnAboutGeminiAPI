# 07.10 File Search a fondo, parte 3: METADATOS personalizados y `metadata_filter` (sintaxis AIP-160: =, >, >=, AND, OR, -/NOT, :).
# Cinco documentos cortos, cada uno con una palabra secreta y metadatos (author texto, year numero, genero texto, tags lista).
# La pregunta pide el secreto de TODOS los documentos; con cada filtro se mira QUE documentos se recuperaron, usando el campo
# `source` de las citas (el texto del chunk) como evidencia, no solo la respuesta del modelo. Tambien: metadatos en la anotacion,
# `documents.get`, y filtros mal escritos o con campos inexistentes. Se borran stores y el archivo de la Files API en finally.
# Ejecutar con `python -u ... > archivo`.

import tempfile
import time
from pathlib import Path

from google import genai

client = genai.Client(http_options={"timeout": 90_000})
S = client.file_search_stores
MODELO = "gemini-3.5-flash-lite"
tmp = Path(tempfile.mkdtemp())
stores, archivos = [], []

DOCS = [  # (secreto, author, year, genero, tags)
    ("coral", "Ana", 1990, "ciencia", ["mar", "vida"]),
    ("bambu", "Ana", 2010, "novela", ["selva"]),
    ("cobre", "Luis", 2005, "ciencia", ["mina", "metal"]),
    ("ambar", "Luis", 2020, "novela", ["bosque"]),
    ("jade", "Ana", 2000, "novela", ["mar"]),  # este entra por IMPORTACION (Files API)
]
SECRETOS = [d[0] for d in DOCS]


def esperar(op):
    while not op.done:
        time.sleep(4)
        op = client.operations.get(op)
    return op


def meta(author, year, genero, tags):
    return [{"key": "author", "string_value": author}, {"key": "year", "numeric_value": year},
            {"key": "genero", "string_value": genero}, {"key": "tags", "string_list_value": {"values": tags}}]


def preguntar(store, filtro):
    tool = {"type": "file_search", "file_search_store_names": [store]}
    if filtro is not None:
        tool["metadata_filter"] = filtro
    try:
        r = client.interactions.create(
            model=MODELO, tools=[tool],
            input="Search the store and list the secret word of EVERY document you can find. Reply only with the words.")
    except Exception as e:
        return None, f"RECHAZADO {getattr(e, 'status_code', None)} {str(e)[:230]}", []
    texto, anot = "", []
    for s in r.steps:
        if s.type == "model_output":
            for b in s.content:
                if b.type == "text":
                    texto += b.text
                    anot += [a.model_dump() for a in (b.annotations or [])]
    return r, texto.strip().replace("\n", " "), anot


try:
    st = S.create(config={"display_name": "T2.3 metadatos"})
    stores.append(st.name)
    for i, (sec, au, yr, ge, tg) in enumerate(DOCS[:4]):
        f = tmp / f"doc{i}.txt"
        f.write_text(f"Libro numero {i}. La palabra secreta de este libro es: {sec}.", encoding="utf-8")
        esperar(S.upload_to_file_search_store(file=str(f), file_search_store_name=st.name,
                                              config={"display_name": f"doc{i}", "custom_metadata": meta(au, yr, ge, tg)}))
    f = tmp / "doc4.txt"
    f.write_text(f"Libro numero 4. La palabra secreta de este libro es: {DOCS[4][0]}.", encoding="utf-8")
    sub = client.files.upload(file=str(f), config={"display_name": "doc4"})
    archivos.append(sub.name)
    esperar(S.import_file(file_search_store_name=st.name, file_name=sub.name, config={"custom_metadata": meta(*DOCS[4][1:])}))
    time.sleep(3)

    docs = list(S.documents.list(parent=st.name))
    print("documentos:", [(d.display_name, d.size_bytes) for d in docs])
    print("documents.get ->", {k: v for k, v in S.documents.get(name=docs[0].name).model_dump().items() if v is not None and k != "name"})

    FILTROS = [
        ("sin filtro", None),
        ('author="Ana"', 'author="Ana"'),
        ("year>2000", "year>2000"),
        ('author="Luis" AND year>2010', 'author="Luis" AND year>2010'),
        ('genero="ciencia" OR year>=2020', 'genero="ciencia" OR year>=2020'),
        ('NOT author="Ana"', 'NOT author="Ana"'),
        ('tags:"mar" (lista)', 'tags:"mar"'),
        ("author=Ana (sin comillas)", "author=Ana"),
        ('color="rojo" (campo inexistente)', 'color="rojo"'),
        ('author="Nadie" (sin coincidencias)', 'author="Nadie"'),
        ("year>2000 AND (sintaxis rota", "year>2000 AND ("),
    ]
    for nombre, filtro in FILTROS:
        r, texto, anot = preguntar(st.name, filtro)
        recup = sorted({s for a in anot for s in SECRETOS if s in a.get("source", "")})
        print(f"\n[{nombre}]\n   respuesta: {texto[:170]}\n   recuperados segun las citas: {recup} | anotaciones={len(anot)}"
              + (f" | tokens={getattr(r.usage, 'total_tokens', '?')}" if r else ""))
        if nombre == "sin filtro" and anot:
            print("   anotacion[0] completa (sin source):", {k: v for k, v in anot[0].items() if k != "source" and v is not None})
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
    print("\nstores que quedan:", [s.name for s in S.list()])
