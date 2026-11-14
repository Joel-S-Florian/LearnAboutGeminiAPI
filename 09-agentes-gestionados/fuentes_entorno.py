# 09.17 Entornos: montar FUENTES al crear el sandbox (environment={"type": "remote", "sources": [...]}).
# Tres tipos: repository (git, max 500 MB), gcs (Cloud Storage, max 2 GB), inline (texto, 1 MB por archivo).
# Se comprueba de DOS formas: lo que cuenta el agente y lo que ve NUESTRO codigo con client.environments
# (get + files.list), que no depende de lo que diga el modelo. Todas las fuentes son publicas (sin credenciales).
# Al final se BORRA el entorno (try/finally) y se prueba que target="/" se rechaza.

from google import genai

client = genai.Client(http_options={"api_version": "v1beta", "timeout": 300_000})
AGENTE = "antigravity-preview-09-2026"
FUENTES = [
    {"type": "repository", "source": "https://github.com/octocat/Spoon-Knife", "target": "/workspace/spoon-knife"},
    {"type": "gcs", "source": "gs://cloud-samples-data/bigquery/us-states/", "target": "/workspace/gcs-data"},
    {"type": "inline", "content": "# Notas\n\n- palabra clave: mangu\n", "target": "/workspace/notas/leeme.md"},
]

env_id = None
try:
    r = client.interactions.create(
        agent=AGENTE,
        agent_config={"type": "antigravity", "max_total_tokens": 80_000},
        input="List every file under /workspace (recursively, with sizes) and tell me the keyword written in notas/leeme.md. Be brief.",
        environment={"type": "remote", "sources": FUENTES},
    )
    env_id = r.environment_id
    print("estado:", r.status, "| entorno:", env_id, "| tokens:", getattr(r.usage, "total_tokens", "?"))
    print("--- lo que cuenta el agente ---\n", (r.output_text or "")[:900])

    print("\n--- lo que ve NUESTRO codigo ---")
    e = client.environments.get(id=env_id)
    print("get:", e.model_dump() if hasattr(e, "model_dump") else e)
    for f in client.environments.files.list(environment=env_id, path="workspace", recursive=True).files:
        if "/.git/" in f.path:  # el clon trae cientos de archivos de .git: se omiten del listado
            continue
        print(f"  {f.type:9} {f.path} {getattr(f, 'size_bytes', '')}")
finally:
    if env_id:
        client.environments.delete(id=env_id)
        print("\nentorno borrado:", env_id)

# target="/" no esta permitido segun la doc: se espera un error 400
try:
    client.interactions.create(
        agent=AGENTE, input="Say OK.",
        environment={"type": "remote", "sources": [{"type": "inline", "content": "x", "target": "/"}]},
    )
    print("\nOJO: target='/' fue ACEPTADO (la doc dice que no se puede)")
except Exception as ex:
    print(f"\ntarget='/' rechazado: {getattr(ex, 'status_code', None)} {str(ex)[:200]}")
