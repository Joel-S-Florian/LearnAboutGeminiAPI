# 07.17 Code execution a fondo, parte 4: MULTI-TURNO (¿persiste el estado del interprete entre turnos?) y LIBRERIAS (¿esta todo lo que lista la doc?).
# Los resultados se leen DIRECTAMENTE de los pasos `code_execution_result` (no del texto del modelo), pidiendole "ejecuta exactamente esto".
#   A) variable y archivo creados en el turno 1 -> ¿existen en el turno 2 (con previous_interaction_id) y en una interaccion NUEVA?
#   B) `import` de cada libreria de la doc (y algunas extra), con version y tiempo       C) `pip install` (la doc: no se pueden instalar librerias)
# Ejecutar con `python -u ... > archivo`.

import time

from google import genai

client = genai.Client(http_options={"api_version": "v1beta", "timeout": 240_000})
MODELO = "gemini-3.5-flash-lite"
TOOLS = [{"type": "code_execution"}]


def ejecutar(codigo, previous=None, titulo=""):
    t0 = time.time()
    try:
        r = client.interactions.create(model=MODELO, input="Use code execution to run EXACTLY this Python code, once, without changing it:\n" + codigo,
                                       tools=TOOLS, **({"previous_interaction_id": previous} if previous else {}))
    except Exception as e:
        print(f"  [{titulo}] FALLO {type(e).__name__} {getattr(e, 'status_code', None)} {str(e)[:200]}")
        return None, []
    res = [s for s in r.steps if s.type == "code_execution_result"]
    print(f"  [{titulo}] {time.time() - t0:.0f} s | llamadas de codigo={sum(s.type == 'code_execution_call' for s in r.steps)} | is_error={[s.is_error for s in res]}")
    return r, res


print("=== A) multi-turno ===")
r1, res1 = ejecutar("x = 42\nopen('/root/memo.txt', 'w').write('hola desde el turno 1')\nprint('turno 1 listo, x =', x)", titulo="turno 1")
for s in res1:
    print("     resultado:", str(s.result)[-160:].replace("\n", " | "))
r2, res2 = ejecutar("print('x =', x)\nprint('archivo:', open('/root/memo.txt').read())", previous=r1.id, titulo="turno 2 (previous_interaction_id)")
for s in res2:
    print("     resultado:", str(s.result)[-200:].replace("\n", " | "))
r3, res3 = ejecutar("import os\nprint('existe memo.txt:', os.path.exists('/root/memo.txt'))\nprint('x definida:', 'x' in globals())", titulo="interaccion NUEVA (sin previous)")
for s in res3:
    print("     resultado:", str(s.result)[-200:].replace("\n", " | "))

print("\n=== B) librerias de la doc ===")
DOC = ["attr", "chess", "contourpy", "fpdf", "geopandas", "imageio", "jinja2", "joblib", "jsonschema", "jsonschema_specifications", "lxml",
       "matplotlib", "mpmath", "numpy", "cv2", "openpyxl", "packaging", "pandas", "PIL", "google.protobuf", "pylatex", "pyparsing", "PyPDF2",
       "dateutil", "docx", "pptx", "reportlab", "sklearn", "scipy", "seaborn", "six", "striprtf", "sympy", "tabulate", "tensorflow", "toolz", "xlrd"]
EXTRA = ["requests", "bs4", "yaml", "plotly", "statsmodels", "nltk", "networkx", "shapely", "torch", "xgboost", "sqlalchemy", "pytest"]


def bloque(lista):
    return ("import importlib, time\nfor n in " + repr(lista) + ":\n    t = time.time()\n    try:\n        m = importlib.import_module(n)\n"
            "        print('OK', n, getattr(m, '__version__', '?'), round(time.time() - t, 1))\n    except Exception as e:\n        print('FALTA', n, type(e).__name__)\n")


ok, falta = [], []
for titulo, lista in (("ligeras", [n for n in DOC if n not in ("tensorflow", "geopandas", "sklearn", "scipy", "cv2")]),
                      ("pesadas", ["tensorflow", "geopandas", "sklearn", "scipy", "cv2"]), ("extra (no estan en la doc)", EXTRA)):
    r, res = ejecutar(bloque(lista), titulo=f"imports {titulo}")
    for s in res:
        for linea in str(s.result).splitlines():
            if linea.startswith("OK"):
                ok.append(linea)
            elif linea.startswith("FALTA"):
                falta.append(linea)
    print(f"     OK: {len([l for l in ok if l.split()[1] in lista])} | FALTA: {[l.split()[1] for l in falta if l.split()[1] in lista]}")
print("\nLINEAS 'OK' (nombre, version, segundos):")
print("  " + " ; ".join(f"{l.split()[1]} {l.split()[2]}" for l in ok))

print("\n=== C) pip install ===")
r, res = ejecutar("import subprocess, sys\np = subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyfiglet'], capture_output=True, text=True, timeout=60)\n"
                  "print('codigo de salida:', p.returncode)\nprint((p.stdout + p.stderr)[-300:])", titulo="pip install pyfiglet")
for s in res:
    print("     resultado:", str(s.result)[-380:].replace("\n", " | "))
