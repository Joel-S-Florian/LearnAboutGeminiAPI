# 09.25 Credencial tipo environment_variable: la variable del sandbox recibe un MARCADOR y el proxy cambia el marcador por
# el secreto real solo en peticiones a los trusted_domains, y solo en las ubicaciones de injection_location.
# Se espera (segun la doc):
#   1) echo $MI_TOKEN                          -> __GEMINI_CRED_<id>__   (no el secreto)
#   2) cabecera hacia httpbin.org (confiable)  -> httpbin recibe el secreto real
#   3) cabecera hacia postman-echo.com         -> rechazada (dominio no confiable)
#   4) marcador en la query hacia httpbin.org  -> rechazada (injection_location solo "header")
# Secreto FALSO. Credencial y entorno se borran en finally.

import time

from google import genai

client = genai.Client(http_options={"api_version": "v1beta", "timeout": 300_000})
CFG = {"type": "antigravity", "model": "gemini-3.5-flash-lite", "max_total_tokens": 50_000}
CID = "estudio-envvar"

PRUEBA = r"""
echo "1) valor de MI_TOKEN dentro del sandbox: $MI_TOKEN"
echo "2) cabecera -> httpbin.org (confiable):"
curl -s --max-time 20 -w '\nHTTP:%{http_code}\n' -H "X-Key: $MI_TOKEN" https://httpbin.org/headers
echo "3) cabecera -> postman-echo.com (NO confiable):"
curl -s --max-time 20 -w '\nHTTP:%{http_code}\n' -H "X-Key: $MI_TOKEN" https://postman-echo.com/headers
echo "4) marcador en la QUERY -> httpbin.org (injection_location solo header):"
curl -s --max-time 20 -w '\nHTTP:%{http_code}\n' "https://httpbin.org/get?k=$MI_TOKEN"
"""

env = None
client.credentials.create(id=CID, type="environment_variable", value="secreto-falso-ENV",
                          trusted_domains=["httpbin.org"], injection_location="header")
try:
    r = client.interactions.create(
        agent="antigravity-preview-09-2026", agent_config=CFG, background=True,
        input="Run this bash script exactly once and paste its whole output verbatim, nothing else:\n" + PRUEBA,
        environment={"type": "remote", "env": {"MI_TOKEN": {"credential": CID}},
                     "network": {"allowlist": [{"domain": "httpbin.org"}, {"domain": "postman-echo.com"}]}},
    )
    env = r.environment_id
    for _ in range(60):
        if r.status not in ("in_progress", "queued"):
            break
        time.sleep(5)
        r = client.interactions.get(id=r.id)
    print(f"estado={r.status} tokens={getattr(r.usage, 'total_tokens', '?')}\n{(r.output_text or '').strip()[:3500]}")
finally:
    if env:
        client.environments.delete(id=env)
    client.credentials.delete(id=CID)
    print("\nquedan entornos:", [x.id[:8] for x in client.environments.list().environments or []],
          "| credenciales:", [x.id for x in client.credentials.list().credentials or []])
