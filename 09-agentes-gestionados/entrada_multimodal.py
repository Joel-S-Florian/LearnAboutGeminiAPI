# 09.6 Entrada multimodal del agente: SOLO text e image, y la imagen debe ir en Base64 ("data").
# La doc dice que audio, video y document no se admiten todavia. Probamos las dos cosas:
#   A) imagen: el chart.png que el propio agente creo en 10.2 (hay que haber corrido descargar_entorno.py)
#   B) documento (CSV): segun la doc debe rechazarse; vemos COMO falla.

import base64
from pathlib import Path

from google import genai

RAIZ = Path(__file__).resolve().parent.parent
GRAFICO = RAIZ / "salidas" / "entorno_58dbb286" / "chart.png"
CSV = RAIZ / "assets" / "ventas_q3.csv"

client = genai.Client(http_options={"api_version": "v1beta", "timeout": 300_000})
CONFIG = {"type": "antigravity", "max_total_tokens": 40_000}

# --- A: imagen en Base64 ---
imagen_b64 = base64.b64encode(GRAFICO.read_bytes()).decode("utf-8")
try:
    r = client.interactions.create(
        agent="antigravity-preview-09-2026",
        input=[
            {"type": "text", "text": "Analyze this chart and summarize the trends in at most 3 lines."},
            {"type": "image", "data": imagen_b64, "mime_type": "image/png"},
        ],
        environment="remote",
        agent_config=CONFIG,
    )
    tokens = r.usage.total_tokens if getattr(r, "usage", None) else "?"
    print("===== A: imagen =====")
    print((r.output_text or "").strip()[:600])
    print(f"-- estado={r.status} tokens={tokens}")
except Exception as e:
    print(f"A fallo: {type(e).__name__} {getattr(e, 'status_code', None)} {str(e)[:300]}")

# --- B: documento (no soportado segun la doc) ---
csv_b64 = base64.b64encode(CSV.read_bytes()).decode("utf-8")
try:
    r = client.interactions.create(
        agent="antigravity-preview-09-2026",
        input=[
            {"type": "text", "text": "Which month has the highest sales in this file?"},
            {"type": "document", "data": csv_b64, "mime_type": "text/csv"},
        ],
        environment="remote",
        agent_config=CONFIG,
    )
    print("\n===== B: documento =====")
    print("ACEPTADO (la doc dice que no):", (r.output_text or "").strip()[:300])
except Exception as e:
    print(f"\n===== B: documento =====\nRECHAZADO: {type(e).__name__} {getattr(e, 'status_code', None)} {str(e)[:400]}")
