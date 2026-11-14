# 09.14, 09.17, 09.18 y 09.19: agente GUARDADO (managed agent): se registra una vez con agents.create y despues
# se invoca por su id, sin repetir la configuracion. Cada invocacion forka el entorno base: parte limpia.
# Pasos de este script (todo con limpieza al final: el agente es un recurso PERSISTENTE en tu proyecto):
#   1. crear el agente desde fuentes (system_instruction + AGENTS.md)      [10.14]
#   2. get y list                                                         [10.19]
#   3. probar un id con prefijo reservado ("gemini-..."), debe fallar     [10.19]
#   4. invocarlo por id                                                   [10.17]
#   5. invocarlo SOBRESCRIBIENDO system_instruction y tools                [10.18]
#   6. borrarlo y comprobar que ya no esta en la lista                    [10.19]

import time

from google import genai

client = genai.Client(http_options={"api_version": "v1beta", "timeout": 300_000})
ID = "estudio-saludador"  # no puede empezar por gemini-, google-, antigravity-, etc.
AGENTS_MD = "End every final answer with the exact line: -- Agent: ALFA --"


def resumen(titulo, r):
    tokens = r.usage.total_tokens if getattr(r, "usage", None) else "?"
    print(f"\n===== {titulo} =====")
    print((r.output_text or "(sin texto)").strip()[:400])
    print(f"-- estado={r.status} tokens={tokens}")


try:
    # 1. Crear (el modelo se fija aqui, en agent_config; en agentes guardados NO se puede cambiar al invocar)
    agente = client.agents.create(
        id=ID,
        description="Agente de estudio: saluda en espanol y firma con un marcador",
        base_agent="antigravity-preview-09-2026",
        agent_config={"type": "antigravity", "model": "gemini-3.5-flash-lite"},
        system_instruction="Always write your final answer in Spanish.",
        base_environment={
            "type": "remote",
            "sources": [{"type": "inline", "target": ".agents/AGENTS.md", "content": AGENTS_MD}],
        },
    )
    print("Creado:", agente.id)

    # 2. get y list
    print("get ->", str(client.agents.get(id=ID))[:300])
    print("list ->", [a.id for a in client.agents.list().agents])

    # 3. Prefijo reservado
    try:
        client.agents.create(id="gemini-prueba", base_agent="antigravity-preview-09-2026")
        print("OJO: 'gemini-prueba' fue ACEPTADO (la doc dice que falla)")
        client.agents.delete(id="gemini-prueba")
    except Exception as e:
        print(f"id con prefijo reservado -> RECHAZADO {getattr(e, 'status_code', None)}: {str(e)[:200]}")

    # 4. Invocar por id
    r = client.interactions.create(agent=ID, input="Greet Ana.", environment="remote")
    resumen("4: invocar por id (esperado: espanol + marcador ALFA)", r)
    time.sleep(30)

    # 5. Sobrescribir system_instruction y tools para ESTA ejecucion (la definicion guardada no cambia)
    r = client.interactions.create(
        agent=ID,
        input="Greet Ana.",
        system_instruction="Answer in English only, in one short line.",
        tools=[{"type": "code_execution"}],
        environment="remote",
    )
    resumen("5: invocar sobrescribiendo system_instruction y tools", r)
finally:
    # 6. Limpieza: borrar el agente (los entornos e interacciones ya creados no se ven afectados)
    try:
        client.agents.delete(id=ID)
        print("\nBorrado:", ID)
    except Exception as e:
        print(f"\nNo se pudo borrar {ID}: {type(e).__name__} {str(e)[:150]}")
    try:
        print("list tras borrar ->", [a.id for a in client.agents.list().agents or []])
    except Exception as e:
        print(f"list fallo: {type(e).__name__} {str(e)[:150]}")
