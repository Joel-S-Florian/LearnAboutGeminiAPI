# 09.21 Red del entorno: (A) network="disabled", (B) refrescar reglas con environment_id (la doc dice que REEMPLAZA),
# (C) comodin "*.example.com" (la doc dice que NO cubre example.com), (D) transform: se inyecta de verdad la cabecera?
# Cada prueba pide al agente varios `curl -w '%{http_code}'` y se comparan los codigos (403 = bloqueado por el proxy).
# Se usan valores FALSOS en transform. Los entornos se guardan al instante (background) y se borran en finally.

import time

from google import genai

client = genai.Client(http_options={"api_version": "v1beta", "timeout": 300_000})
CFG = {"type": "antigravity", "model": "gemini-3.5-flash-lite", "max_total_tokens": 40_000}
creados = []


def curl_cmds(urls):
    return ("Run these shell commands and report each HTTP code labelled by URL (000 = could not connect). One line.\n"
            + "\n".join(f"curl -s -o /dev/null -w '%{{http_code}}' --max-time 15 {u}" for u in urls))


def correr(titulo, input, environment):
    r = client.interactions.create(agent="antigravity-preview-09-2026", agent_config=CFG, background=True,
                                   input=input, environment=environment)
    if r.environment_id:
        creados.append(r.environment_id)
    for _ in range(60):
        if r.status not in ("in_progress", "queued"):
            break
        time.sleep(5)
        r = client.interactions.get(id=r.id)
    print(f"\n[{titulo}] estado={r.status} tokens={getattr(r.usage, 'total_tokens', '?')}\n  {(r.output_text or '').strip()[:400]}")
    return r


try:
    U = ["https://pypi.org", "https://example.com"]
    # A) desactivada
    correr("A network=disabled", curl_cmds(U), {"type": "remote", "network": "disabled"})

    # B) refrescar: 1a vez solo pypi.org; 2a vez, MISMO entorno, solo example.com
    b1 = correr("B1 allowlist solo pypi.org", curl_cmds(U),
                {"type": "remote", "network": {"allowlist": [{"domain": "pypi.org"}]}})
    correr("B2 mismo entorno, allowlist solo example.com", curl_cmds(U),
           {"type": "remote", "environment_id": b1.environment_id,
            "network": {"allowlist": [{"domain": "example.com"}]}})

    # C) comodin de subdominios
    correr("C allowlist '*.example.com'", curl_cmds(["https://example.com", "https://www.example.com"]),
           {"type": "remote", "network": {"allowlist": [{"domain": "*.example.com"}]}})

    # D) transform: httpbin devuelve las cabeceras que RECIBE; si sale X-Prueba, el proxy la inyecto
    correr("D transform", "Run: curl -s --max-time 20 https://httpbin.org/headers  and show the JSON it returns, verbatim.",
           {"type": "remote", "network": {"allowlist": [
               {"domain": "httpbin.org", "transform": {"X-Prueba": "valor-falso-123"}}]}})
finally:
    for i in set(creados):
        client.environments.delete(id=i)
    print("\nentornos borrados:", len(set(creados)), "| quedan:", [x.id[:8] for x in client.environments.list().environments or []])
