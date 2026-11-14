# 07.14 Code execution a fondo, parte 1: PASOS, ERRORES y LIMITES. Segun la doc: solo Python, 30 s de ejecucion maxima, el modelo puede
# regenerar el codigo hasta 5 veces si hay error, y los pasos son `code_execution_call` (arguments.code) y `code_execution_result` (result).
# Se mira la ESTRUCTURA real de los pasos y cinco comportamientos:
#   1 la suma de los primeros 50 primos (ejemplo de la doc; resultado esperado 5117)    2 un error obvio (1/0): cuantas veces reintenta?
#   3 un sleep de 40 s (el limite es 30)    4 pedir bash/JavaScript (la doc: solo se ejecuta Python)    5 acceso a la red
# Se imprime cada paso (codigo y resultado recortados). Ejecutar con `python -u ... > archivo`.

import json
import time

from google import genai

client = genai.Client(http_options={"api_version": "v1beta", "timeout": 120_000})
MODELO = "gemini-3.5-flash-lite"


def correr(titulo, prompt, mostrar_estructura=False):
    print(f"\n===== {titulo} =====")
    t0 = time.time()
    try:
        r = client.interactions.create(model=MODELO, input=prompt, tools=[{"type": "code_execution"}])
    except Exception as e:
        print(f"  FALLO: {type(e).__name__} {getattr(e, 'status_code', None)} {str(e)[:260]}")
        return None
    print(f"  {time.time() - t0:.0f} s | estado={r.status} | tokens={getattr(r.usage, 'total_tokens', '?')} | pasos={[s.type for s in r.steps]}")
    n_codigo = 0
    for s in r.steps:
        if s.type == "code_execution_call":
            n_codigo += 1
            d = s.model_dump()
            if mostrar_estructura and n_codigo == 1:
                print("  estructura del paso call:", {k: (type(v).__name__, (str(v)[:60] if k != "signature" else len(v or ""))) for k, v in d.items() if v is not None})
            print(f"  [call #{n_codigo}] lenguaje={getattr(s.arguments, 'language', None)} codigo={str(s.arguments.code)[:140]!r}")
        elif s.type == "code_execution_result":
            d = s.model_dump()
            if mostrar_estructura:
                print("  estructura del paso result:", {k: (type(v).__name__, (str(v)[:60] if k != "signature" else len(v or ""))) for k, v in d.items() if v is not None})
            print(f"  [result] is_error={d.get('is_error')} resultado={str(s.result)[:200]!r}")
    print("  RESPUESTA:", (r.output_text or "")[:260].replace("\n", " "))
    print(f"  llamadas de codigo: {n_codigo}")
    return r


correr("1 primos (doc)", "What is the sum of the first 50 prime numbers? Generate and run code for the calculation, and make sure you get all 50.", mostrar_estructura=True)
correr("2 error obvio", "Use code execution to run exactly this Python code and tell me what happened: print(1/0)")
correr("3 sleep de 40 s", "Use code execution to run exactly this Python code and tell me the output and how long it took: import time; time.sleep(40); print('listo')")
correr("4 bash", "Use code execution to run this bash command and tell me its output: echo hola desde bash")
correr("5 red", "Use code execution to try to download https://example.com with Python (urllib) and tell me the HTTP status code or the exact error.")
