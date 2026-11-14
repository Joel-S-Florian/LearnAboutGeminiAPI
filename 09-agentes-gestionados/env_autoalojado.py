# 09.33 Entornos autoalojados (self-hosted): SOLO la parte de la API, SIN instalar el CLI `gemini-api` ni conectar ningun runtime.
# Segun la doc: POST /v1beta/environments {"mode": "self_hosted"} devuelve un id y una `environment_key` de UN SOLO USO; despues hay que
# ejecutar `gemini-api environments connect` en TU sandbox con esa clave. NO se hace aqui: en modo local el CLI ejecuta execute_bash
# directamente en el PC de quien lo usa. Se prueba: (1) crear (el SDK 3.2.0 no acepta mode=, se usa REST), (2) get/list/files,
# (3) que pasa si se usa un entorno autoalojado SIN runtime conectado (en segundo plano, se espera <=20 s y se cancela), (4) borrar.
# La environment_key es un SECRETO: nunca se imprime. Ejecutar con `python -u ... > archivo` (ver la leccion de Deep Research).

import os
import time

import requests
from google import genai

BASE = "https://generativelanguage.googleapis.com/v1beta"
HDR = {"x-goog-api-key": os.environ["GEMINI_API_KEY"], "Content-Type": "application/json"}  # la clave nunca se imprime
client = genai.Client(http_options={"api_version": "v1beta", "timeout": 30_000})
env_id = None
iid = None


def corto(r):
    return f"{r.status_code} {r.text[:230]!r}"


try:
    # 1) crear el entorno autoalojado por REST
    r = requests.post(f"{BASE}/environments", headers=HDR, json={"mode": "self_hosted"}, timeout=30)
    print("1) POST /environments {'mode':'self_hosted'} ->", r.status_code)
    if r.status_code != 200:
        raise SystemExit("   no se pudo crear: " + corto(r))
    data = r.json()
    env_id = data["id"]
    print("   claves de la respuesta:", sorted(data.keys()), "| environment_key presente:", "environment_key" in data,
          "| longitud:", len(data.get("environment_key", "")), "(valor NO impreso)")
    print("   resto de campos:", {k: v for k, v in data.items() if k != "environment_key"})

    # 2) get, list y archivos
    g = client.environments.get(id=env_id)
    print("\n2) get:", {k: v for k, v in g.model_dump().items() if v is not None})
    print("   aparece en list():", env_id in [e.id for e in client.environments.list(page_size=50).environments or []])
    try:
        fs = client.environments.files.list(environment=env_id, path="").files
        print("   files.list ->", [f.path for f in fs or []])
    except Exception as e:
        print("   files.list -> fallo:", getattr(e, "status_code", None), str(e)[:200])

    # 3) usarlo sin runtime conectado (segundo plano; cancelar a los 20 s)
    t0 = time.time()
    try:
        i = client.interactions.create(agent="antigravity-preview-09-2026", background=True, environment=env_id,
                                       agent_config={"type": "antigravity", "model": "gemini-3.5-flash-lite", "max_total_tokens": 20_000},
                                       input="Run `echo hola` in the shell and tell me the output.")
        iid = i.id
        print(f"\n3) interaccion creada en {time.time() - t0:.1f} s, estado inicial={i.status}")
        for _ in range(4):
            time.sleep(5)
            i = client.interactions.get(id=iid)
            print(f"   +{time.time() - t0:.0f} s estado={i.status} pasos={[getattr(s, 'type', None) for s in i.steps or []]}")
            if i.status not in ("in_progress", "queued"):
                break
        print("   texto:", (i.output_text or "")[:300].replace("\n", " "), "| error:", str(getattr(i, "error", None))[:250])
    except Exception as e:
        print("\n3) usar el entorno sin runtime -> fallo:", type(e).__name__, getattr(e, "status_code", None), str(e)[:300])
finally:
    if iid:
        try:
            st = client.interactions.get(id=iid).status
            if st in ("in_progress", "queued"):
                client.interactions.cancel(id=iid)
                print("   interaccion cancelada")
            client.interactions.delete(id=iid)
        except Exception as e:
            print("   limpieza de la interaccion:", getattr(e, "status_code", None), str(e)[:100])
    if env_id:
        d = requests.delete(f"{BASE}/environments/{env_id}", headers=HDR, timeout=30)
        print("\n4) DELETE environment ->", d.status_code)
    print("quedan entornos:", [x.id[:8] for x in client.environments.list().environments or []])
