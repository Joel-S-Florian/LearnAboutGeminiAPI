# 09.12 y 09.13 Personalizar el agente EN LINEA (sin registrar nada): tres capas, todas en la misma llamada
#   1. system_instruction            texto suelto para esta llamada
#   2. .agents/AGENTS.md             instrucciones largas; el agente lo carga solo como instrucciones del sistema
#   3. .agents/skills/<nombre>/SKILL.md   una "habilidad" que el agente descubre y puede usar
# AGENTS.md y SKILL.md se montan en el sandbox con "environment": {"type": "remote", "sources": [...]}
# (source tipo "inline": target = ruta dentro del sandbox, content = texto del archivo).
# La doc dice que system_instruction y AGENTS.md son ADITIVOS: se aplican los dos.
# Para VER cada capa usamos marcadores facilmente detectables en la respuesta.

import time

from google import genai

client = genai.Client(http_options={"api_version": "v1beta", "timeout": 300_000})
CONFIG = {"type": "antigravity", "model": "gemini-3.5-flash-lite", "max_total_tokens": 40_000}
TAREA = "Greet Ana."

SYSTEM = "Always write your final answer in Spanish."  # capa 1: idioma de la respuesta
AGENTS_MD = "End every final answer with the exact line: -- Agent: ALFA --"  # capa 2: marcador al final
SKILL_MD = (  # capa 3: habilidad (front matter con name y description, luego instrucciones)
    "---\nname: greeter\ndescription: Greeting files\n---\n# Greeter\n\n"
    "When asked to greet someone, create the file /workspace/greeting.txt containing exactly "
    "'Hello, <NAME>, from skill GREETER' and report the file path."
)


def correr(titulo, **extra):
    r = client.interactions.create(agent="antigravity-preview-09-2026", input=TAREA, agent_config=CONFIG, **extra)
    tokens = r.usage.total_tokens if getattr(r, "usage", None) else "?"
    print(f"\n===== {titulo} =====")
    print((r.output_text or "(sin texto)").strip()[:500])
    print(f"-- estado={r.status} tokens={tokens}")
    # nombres de las herramientas internas usadas (p. ej. escritura de archivos)
    llamadas = [(s.name, str(getattr(s, "arguments", ""))[:90]) for s in (r.steps or []) if s.type == "function_call"]
    print("-- function_call del entorno:", llamadas)


correr("A: sin personalizar", environment="remote")
time.sleep(30)
correr(
    "B: system_instruction + AGENTS.md + SKILL.md",
    system_instruction=SYSTEM,
    environment={
        "type": "remote",
        "sources": [
            {"type": "inline", "target": ".agents/AGENTS.md", "content": AGENTS_MD},
            {"type": "inline", "target": ".agents/skills/greeter/SKILL.md", "content": SKILL_MD},
        ],
    },
)
