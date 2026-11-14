# 09.11 Limites del agente Antigravity segun la doc, comprobados uno por uno con una tarea minima
# ("responde OK"). Por cada caso se ve si la API lo RECHAZA (y con que mensaje) o lo ACEPTA.
# Segun la doc: temperature, top_p, top_k, stop_sequences y max_output_tokens dan 400; tampoco hay salida
# estructurada ni las herramientas file_search, computer_use y google_maps.
# Si un caso es ACEPTADO se ejecuta un agente de verdad (gasta tokens): por eso el tope es pequeno.

from google import genai

client = genai.Client(http_options={"api_version": "v1beta", "timeout": 300_000})
BASE = dict(
    agent="antigravity-preview-09-2026",
    input="Reply with the single word OK. Do not use any tool.",
    environment="remote",
)
CONFIG = {"type": "antigravity", "model": "gemini-3.5-flash-lite", "max_total_tokens": 5_000}

CASOS = {
    "temperature": dict(generation_config={"temperature": 0.5}),
    "top_p": dict(generation_config={"top_p": 0.9}),
    "top_k": dict(generation_config={"top_k": 40}),
    "stop_sequences": dict(generation_config={"stop_sequences": ["STOP"]}),
    "max_output_tokens": dict(generation_config={"max_output_tokens": 100}),
    "salida estructurada": dict(
        response_format={
            "type": "text",
            "mime_type": "application/json",
            "schema": {"type": "object", "properties": {"answer": {"type": "string"}}, "required": ["answer"]},
        }
    ),
    "tool file_search": dict(tools=[{"type": "file_search", "file_search_store_names": ["fileSearchStores/no-existe"]}]),
    "tool google_maps": dict(tools=[{"type": "google_maps"}]),
    "tool computer_use": dict(tools=[{"type": "computer_use", "environment": "browser"}]),
}

for nombre, extra in CASOS.items():
    try:
        r = client.interactions.create(agent_config=CONFIG, **BASE, **extra)
        tokens = r.usage.total_tokens if getattr(r, "usage", None) else "?"
        print(f"{nombre:<20} ACEPTADO  estado={r.status} tokens={tokens} salida={(r.output_text or '').strip()[:60]!r}")
    except Exception as e:
        msg = str(e).replace("\n", " ")
        print(f"{nombre:<20} RECHAZADO {getattr(e, 'status_code', None)} {type(e).__name__}: {msg[:200]}")
