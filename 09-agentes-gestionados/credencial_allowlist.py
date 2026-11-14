# 09.24 Credencial en la allowlist: {"domain": "httpbin.org", "credential": "<id>"}. El proxy inyecta la cabecera.
# httpbin.org/headers devuelve las cabeceras que RECIBE, asi se ve lo que llego por la red. Todo con tokens FALSOS.
#   1) bearer_token por defecto           -> se espera  Authorization: Bearer <token>
#   2) header_name + prefix=""            -> se espera  X-Api-Token: <token>
#   3) credential + transform (misma clave) -> la doc dice que GANA el transform; REAL: 400 (ver 3b)
#   4) credencial inexistente en la allowlist -> que pasa?
# Ademas, en el caso 1 se mira si el secreto aparece DENTRO del sandbox (variables de entorno y archivos).
# Credenciales y entornos se borran en finally.

import time

from google import genai

client = genai.Client(http_options={"api_version": "v1beta", "timeout": 300_000})
CFG = {"type": "antigravity", "model": "gemini-3.5-flash-lite", "max_total_tokens": 40_000}
creds, envs = [], []
ECO = "Run `curl -s --max-time 20 https://httpbin.org/headers` and paste the JSON it returns verbatim."


def correr(titulo, input, allow):
    try:
        r = client.interactions.create(agent="antigravity-preview-09-2026", agent_config=CFG, background=True, input=input,
                                       environment={"type": "remote", "network": {"allowlist": allow}})
    except Exception as e:
        print(f"\n[{titulo}] RECHAZADO: {getattr(e, 'status_code', None)} {str(e)[:250]}")
        return None
    if r.environment_id:
        envs.append(r.environment_id)
    for _ in range(60):
        if r.status not in ("in_progress", "queued"):
            break
        time.sleep(5)
        r = client.interactions.get(id=r.id)
    print(f"\n[{titulo}] estado={r.status} tokens={getattr(r.usage, 'total_tokens', '?')}\n{(r.output_text or '').strip()[:700]}")
    return r


try:
    client.credentials.create(id="estudio-bearer", type="bearer_token", token="token-falso-AAA"); creds.append("estudio-bearer")
    client.credentials.create(id="estudio-custom", type="bearer_token", token="token-falso-BBB",
                              header_name="X-Api-Token", prefix=""); creds.append("estudio-custom")

    correr("1 bearer por defecto + busca el secreto dentro del sandbox",
           ECO + "\nThen run `env | grep -c token-falso; grep -rIl token-falso /workspace /home /tmp 2>/dev/null | head -3; echo fin` "
           "and paste that output too.",
           [{"domain": "httpbin.org", "credential": "estudio-bearer"}])
    correr("2 header_name=X-Api-Token, prefix vacio", ECO, [{"domain": "httpbin.org", "credential": "estudio-custom"}])
    correr("3 credential + transform (misma clave Authorization)", ECO,
           [{"domain": "httpbin.org", "credential": "estudio-bearer", "transform": {"Authorization": "Bearer DESDE-TRANSFORM"}}])
    # 3b) aislado despues del 400 del caso 3: misma regla pero el transform usa OTRA clave -> se acepta y suma la cabecera
    correr("3b credential + transform (clave distinta X-Extra)", ECO,
           [{"domain": "httpbin.org", "credential": "estudio-bearer", "transform": {"X-Extra": "extra-123"}}])
    correr("4 credencial inexistente", ECO, [{"domain": "httpbin.org", "credential": "no-existe-xyz"}])
finally:
    for e in set(envs):
        client.environments.delete(id=e)
    for c in creds:
        client.credentials.delete(id=c)
    print("\nquedan entornos:", [x.id[:8] for x in client.environments.list().environments or []],
          "| credenciales:", [x.id for x in client.credentials.list().credentials or []])
