# 09.8 MCP remoto en el agente: registras un servidor MCP en tools y el agente llama a sus herramientas.
# Campos del tool: type="mcp_server", name (minuscula/alfanumerico, patron ^[a-z0-9_-]+$), url,
# headers (opcional: autenticacion) y allowed_tools (opcional: lista de herramientas permitidas).
# Solo servidores "Streamable HTTP" (SSE no). Probamos dos casos:
#   A) nombre valido en minuscula (servidor demo de la propia doc)
#   B) nombre con MAYUSCULA: la doc dice que da un 400 generico; vemos el mensaje real.
# Del tema 08.12 aprendimos que este servidor exige fechas y que el modelo las inventa si no se las das.

from google import genai

client = genai.Client(http_options={"api_version": "v1beta", "timeout": 300_000})
CONFIG = {"type": "antigravity", "max_total_tokens": 40_000}
URL = "https://gemini-api-demos.uc.r.appspot.com/mcp"  # servidor de demostracion de la doc de Gemini


def correr(titulo, nombre):
    try:
        r = client.interactions.create(
            agent="antigravity-preview-09-2026",
            input="What is the weather in Tokyo today, 2026-11-14? Answer in one line.",
            environment="remote",
            tools=[{"type": "mcp_server", "name": nombre, "url": URL}],
            agent_config=CONFIG,
        )
    except Exception as e:
        print(f"\n===== {titulo} (name={nombre!r}) =====")
        print(f"RECHAZADO: {type(e).__name__} {getattr(e, 'status_code', None)} {str(e)[:350]}")
        return
    print(f"\n===== {titulo} (name={nombre!r}) =====")
    print((r.output_text or "").strip()[:400])
    tokens = r.usage.total_tokens if getattr(r, "usage", None) else "?"
    print(f"-- estado={r.status} tokens={tokens}")
    for s in r.steps or []:
        if s.type.startswith("mcp_server_tool"):
            print(f"   [{s.type}] {str(s.model_dump(exclude={'signature'}))[:260]}")


correr("A: nombre valido", "weather")
correr("B: nombre con mayuscula", "Weather")
