# Control de 09.16/09.18: al sobrescribir la red de un agente guardado con solo example.com, pypi.org SIGUIO
# accesible (200). Se prueba aqui el agente BASE (sin agente guardado) con allowlist solo example.com, para
# separar dos explicaciones posibles: (a) la sobrescritura no reemplaza sino que suma a las reglas guardadas,
# (b) pypi.org esta permitido siempre que haya reglas de red (p. ej. por ser un gestor de paquetes).
# Si pypi.org sale 200 aqui, gana (b); si sale 403, gana (a).

from google import genai

client = genai.Client(http_options={"api_version": "v1beta", "timeout": 300_000})
CURL = (
    "Run these two shell commands and report the two HTTP codes, labelled by site (000 means it could not connect):\n"
    "curl -s -o /dev/null -w '%{http_code}' --max-time 15 https://pypi.org\n"
    "curl -s -o /dev/null -w '%{http_code}' --max-time 15 https://example.com\n"
    "Answer in one line."
)

r = client.interactions.create(
    agent="antigravity-preview-09-2026",
    input=CURL,
    environment={"type": "remote", "network": {"allowlist": [{"domain": "example.com"}]}},
    agent_config={"type": "antigravity", "model": "gemini-3.5-flash-lite", "max_total_tokens": 30_000},
)
tokens = r.usage.total_tokens if getattr(r, "usage", None) else "?"
print("Agente base, allowlist solo example.com ->", (r.output_text or "").strip()[:200], f"| estado={r.status} tokens={tokens}")
