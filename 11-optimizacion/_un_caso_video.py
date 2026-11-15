# Ayuda de video_agentico.py: UN caso por proceso (el driver lo corta si se cuelga).
# Uso: python _un_caso_video.py MODELO PROCESSING(none|static|agentic|<otro>) ID_PREGUNTA URI_ARCHIVO
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # la consola de Windows (cp1252) no imprime flechas ni simbolos

from google import genai

modelo, processing, pid, uri = sys.argv[1:5]
PREGUNTAS = {
    "resumen": "Summarize this video in two sentences.",
    "terminal": "In the terminal scene, what is the output line shown right after the command 'hook_con_error_de_sintaxis.py'? Quote it exactly.",
    "cifras": "In the statistics scene near the end, list the four big numbers with their labels.",
}
bloque = {"type": "video", "uri": uri, "mime_type": "video/mp4"}
if processing != "none":
    bloque["processing"] = processing
c = genai.Client(http_options={"api_version": "v1beta", "timeout": 120_000})
t0 = time.time()
try:
    r = c.interactions.create(model=modelo, input=[bloque, {"type": "text", "text": PREGUNTAS[pid]}])
    u = r.usage
    uso = {k: getattr(u, k, None) for k in ("total_input_tokens", "total_tool_use_tokens", "total_thought_tokens", "total_output_tokens", "total_tokens")}
    print(f"OK {modelo} processing={processing} {pid}: {time.time() - t0:.0f} s | {uso} | pasos={[s.type for s in r.steps]}")
    print("   RESPUESTA:", (r.output_text or "").replace("\n", " ")[:330])
except Exception as e:
    print(f"FALLO {modelo} processing={processing} {pid}: {getattr(e, 'status_code', None)} {type(e).__name__}: {str(e)[:330]} ({time.time() - t0:.0f} s)")
