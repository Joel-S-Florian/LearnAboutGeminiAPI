# 09.22 Software preinstalado del entorno: se COMPRUEBA la tabla de la doc (Ubuntu, Python 3.12, Node 22,
# herramientas UNIX, paquetes de Python y de Node) ejecutando un script en el sandbox, y se prueba la
# persistencia: un `pip install` en una interaccion sigue disponible al reutilizar el mismo environment_id.
# El agente ejecuta el script y pega la salida tal cual. El entorno se guarda al instante y se borra en finally.

import time

from google import genai

client = genai.Client(http_options={"api_version": "v1beta", "timeout": 300_000})
CFG = {"type": "antigravity", "model": "gemini-3.5-flash-lite", "max_total_tokens": 60_000}
creados = []

SCRIPT = r"""
. /etc/os-release; echo "OS: $PRETTY_NAME"; python3 --version; node --version
for t in curl wget git rsync unzip rg fd fdfind gawk bc tree which lsof htop jq ip ps gcloud ast-grep; do
  command -v $t >/dev/null 2>&1 && echo "OK $t" || echo "FALTA $t"; done
python3 - <<'PY'
from importlib.metadata import version, PackageNotFoundError
for p in ["numpy","pandas","requests","google-genai","beautifulsoup4","pyyaml","ast-grep-cli","matplotlib"]:
    try: print("py OK", p, version(p))
    except PackageNotFoundError: print("py FALTA", p)
PY
npm ls -g --depth=0 2>/dev/null | tail -n +2
"""


def correr(titulo, texto, environment):
    r = client.interactions.create(agent="antigravity-preview-09-2026", agent_config=CFG, background=True,
                                   input=texto, environment=environment)
    if r.environment_id:
        creados.append(r.environment_id)
    for _ in range(60):
        if r.status not in ("in_progress", "queued"):
            break
        time.sleep(5)
        r = client.interactions.get(id=r.id)
    print(f"\n[{titulo}] estado={r.status} tokens={getattr(r.usage, 'total_tokens', '?')}\n{(r.output_text or '').strip()[:2500]}")
    return r


try:
    a = correr("1 tabla de la doc", "Run this bash script exactly once and paste its output verbatim, nothing else:\n" + SCRIPT, "remote")
    b = correr("2 pip install", "Run `pip install pyfiglet` and reply with only the installed version line.",
               {"type": "remote", "environment_id": a.environment_id})
    correr("3 persiste?", "Run `python3 -c \"import pyfiglet; print('IMPORTA OK')\"` and paste the output verbatim.",
           {"type": "remote", "environment_id": a.environment_id})
finally:
    for i in set(creados):
        client.environments.delete(id=i)
    print("\nquedan:", [x.id[:8] for x in client.environments.list().environments or []])
