# 11.5 Procesamiento AGENTICO de video. La doc: por defecto TODOS los modelos usan procesamiento ESTATICO (1 fotograma por segundo); con
# `processing: "agentic"` (Interactions API) el modelo lee primero la transcripcion y carga segmentos visuales con mas fotogramas/resolucion solo
# donde hace falta. Ahorra hasta un 88 % de tokens de entrada en videos LARGOS (> 5-10 min) o preguntas puntuales; en clips cortos (< 5 min) o resumenes
# generales conviene el estatico (menos latencia y menos sobrecarga). Gasta tokens de razonamiento (`total_thought_tokens`) y de herramientas
# (`total_tool_use_tokens`). Modelos: Gemini 4, 3.8 Flash, 3.6 Flash y 3.5 Flash-Lite; el resto devuelve error.
# MATERIAL: el video de 36 s del post de LinkedIn (sin audio), con contenido CONOCIDO: titulo, 6 tarjetas de temas, una terminal con 5 lineas y 4 cifras
# (41 commits, 98 scripts, 10 modulos, 107 notas). Se sube a la Files API de tu proyecto y se BORRA al final.
# Cada llamada se ejecuta en su propio proceso con corte (lecciones sobre cuelgues). Ejecutar con `python -u ... > archivo`.

import os
import subprocess
import sys
import time
from pathlib import Path

from google import genai

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
VIDEO = Path(r"C:\Users\Joel S. Florian\Videos\Mercado Laboral\03_video_resumen_gemini.mp4")
AQUI = Path(__file__).resolve().parent
client = genai.Client(http_options={"api_version": "v1beta", "timeout": 120_000})

f = client.files.upload(file=str(VIDEO), config={"display_name": "estudio-video-36s", "mime_type": "video/mp4"})
try:
    for _ in range(30):
        f = client.files.get(name=f.name)
        if str(f.state).endswith("ACTIVE"):
            break
        time.sleep(3)
    print(f"archivo: {f.name} | estado={f.state} | {VIDEO.stat().st_size / 1e6:.1f} MB | duracion segun la API: {getattr(f, 'video_metadata', None)}")

    def caso(modelo, processing, pid, corte=170):
        try:
            out = subprocess.run([sys.executable, "-u", str(AQUI / "_un_caso_video.py"), modelo, processing, pid, f.uri],
                                 capture_output=True, text=True, timeout=corte, encoding="utf-8", errors="replace", env={**os.environ, "PYTHONIOENCODING": "utf-8"}).stdout
            print("\n".join(l for l in out.splitlines() if "Warning" not in l and "warnings.warn" not in l))
        except subprocess.TimeoutExpired:
            print(f"CORTADO a los {corte} s: {modelo} processing={processing} {pid}")

    print("\n=== 1) gemini-3.5-flash-lite: sin parametro / static / agentic, tres preguntas ===")
    for pid in ("resumen", "terminal", "cifras"):
        for processing in ("none", "static", "agentic"):
            caso("gemini-3.5-flash-lite", processing, pid)
    print("\n=== 2) modelos que NO soportan agentico ===")
    caso("gemini-2.5-flash", "agentic", "terminal")
    caso("gemini-2.5-flash", "none", "terminal")
    print("\n=== 3) valor invalido ===")
    caso("gemini-3.5-flash-lite", "turbo", "terminal")
finally:
    client.files.delete(name=f.name)
    print("\narchivo de la Files API borrado:", f.name)
