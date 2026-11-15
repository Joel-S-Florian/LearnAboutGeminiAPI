# RESULTADO (2026-11-14): en el nivel gratuito NO se puede crear NINGUN lote (inline, archivo ni embeddings): 400 FAILED_PRECONDITION
# "Precondition check failed." en todos los modelos probados. Este script solo sirve para repetir el sondeo cuando haya facturacion.
# Ayuda de batch_api.py (ya no existe; este es el unico script de O3): UN paso por proceso (se corta con `timeout` del sistema). Uso: python _batch_uno.py ACCION [args]
#   crear_inline MODELO | estado NOMBRE | cancelar NOMBRE | borrar NOMBRE | listar
import json
import sys
import time

from google import genai

c = genai.Client(http_options={"api_version": "v1beta", "timeout": 40_000})
accion = sys.argv[1]
PREGUNTAS = ["Tell me a one-sentence joke.", "Why is the sky blue? One sentence.", "Name three primary colors, comma separated."]
t0 = time.time()
try:
    if accion == "crear_inline":
        modelo = sys.argv[2]
        reqs = [{"contents": [{"parts": [{"text": q}], "role": "user"}]} for q in PREGUNTAS]
        job = c.batches.create(model=modelo, src=reqs, config={"display_name": "estudio-inline"})
        print("CREADO", job.name, "| estado:", job.state.name if job.state else job.state, f"| {time.time() - t0:.1f} s")
        print("campos del job:", sorted(k for k, v in job.model_dump().items() if v is not None))
    elif accion == "crear_archivo":
        modelo = sys.argv[2]
        import tempfile
        ruta = tempfile.mktemp(suffix=".jsonl")
        with open(ruta, "w", encoding="utf-8") as f:
            for i, q in enumerate(PREGUNTAS, 1):
                f.write(json.dumps({"key": f"request-{i}", "request": {"contents": [{"parts": [{"text": q}]}]}}) + chr(10))
        sub = c.files.upload(file=ruta, config={"display_name": "estudio-batch", "mime_type": "jsonl"})
        print("archivo subido:", sub.name)
        try:
            job = c.batches.create(model=modelo, src=sub.name, config={"display_name": "estudio-archivo"})
            print("CREADO", job.name, "| estado:", job.state.name)
        finally:
            c.files.delete(name=sub.name)
    elif accion == "crear_embeddings":
        job = c.batches.create_embeddings(model=sys.argv[2], src={"inlined_requests": {"contents": [{"parts": [{"text": q}]} for q in PREGUNTAS]}}, config={"display_name": "estudio-emb"})
        print("CREADO", job.name, "| estado:", job.state.name)
    elif accion == "invalido":
        caso = sys.argv[2]
        if caso == "modelo_falso":
            c.batches.create(model="gemini-no-existe", src=[{"contents": [{"parts": [{"text": "hola"}], "role": "user"}]}])
        elif caso == "lista_vacia":
            c.batches.create(model="gemini-3.5-flash-lite", src=[])
        elif caso == "peticion_rota":
            c.batches.create(model="gemini-3.5-flash-lite", src=[{"contenido": "esto no es una GenerateContentRequest"}])
        elif caso == "archivo_inexistente":
            c.batches.create(model="gemini-3.5-flash-lite", src="files/no-existe-123")
    elif accion == "estado":
        job = c.batches.get(name=sys.argv[2])
        d = job.model_dump()
        print("ESTADO", job.state.name, "| stats:", d.get("completion_stats") or d.get("batch_stats"), f"| {time.time() - t0:.1f} s")
        if job.state.name == "JOB_STATE_SUCCEEDED" and job.dest and job.dest.inlined_responses:
            for i, r in enumerate(job.dest.inlined_responses, 1):
                print(f"  respuesta {i}:", (r.response.text if r.response else f"ERROR {r.error}")[:110].replace("\n", " "))
        if job.error:
            print("  error:", job.error)
    elif accion == "cancelar":
        c.batches.cancel(name=sys.argv[2]); print("CANCELADO", sys.argv[2])
    elif accion == "borrar":
        c.batches.delete(name=sys.argv[2]); print("BORRADO", sys.argv[2])
    elif accion == "listar":
        jobs = list(c.batches.list(config={"page_size": 20}))
        print("JOBS:", [(j.name, j.state.name, j.display_name) for j in jobs])
except Exception as e:
    print(f"FALLO {accion}: {getattr(e, 'status_code', None)} {type(e).__name__}: {str(e)[:420]} ({time.time() - t0:.1f} s)")
