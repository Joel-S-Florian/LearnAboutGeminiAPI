# 08.12 MCP remoto (Model Context Protocol): en vez de declarar TUS funciones, le das al modelo la URL
# de un servidor MCP y es GOOGLE quien se conecta a ese servidor, descubre sus herramientas y las llama.
# Tu codigo no ejecuta nada ni hace bucle: no hay function_call que atender.
# Restricciones de la doc: solo servidores "Streamable HTTP" (SSE no); el nombre sin "-" (usa snake_case).
# Campos del tool: type="mcp_server", name, url, headers (p. ej. tokens), allowed_tools (restringe cuales).

from google import genai

MODELOS = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.6-flash"]

client = genai.Client(http_options={"timeout": 90_000})

interaction = None
for modelo in MODELOS:
    try:
        interaction = client.interactions.create(
            model=modelo,
            # Sin fecha en el prompt el modelo INVENTO fechas (2023, 2024, 2025) y el servidor fallo con
            # "Forecast failed with status 400". Le damos la fecha de hoy.
            input="Check the weather in San Francisco for today, 2026-11-14.",
            tools=[
                {
                    "type": "mcp_server",
                    "name": "weather",
                    # servidor MCP de demostracion de la propia doc de Gemini
                    "url": "https://gemini-api-demos.uc.r.appspot.com/mcp",
                }
            ],
        )
        print(f"Modelo usado: {modelo}\n")
        break
    except Exception as e:
        print(f"[{modelo}] fallo: {type(e).__name__} {getattr(e, 'status_code', None)} {str(e)[:200]}")

if interaction is None:
    raise SystemExit("Ningun modelo respondio.")

# Pasos: busca los que corresponden al servidor MCP (nombres exactos: no verificados antes de ejecutar)
print("Tipos de pasos:", [s.type for s in interaction.steps])
# Depuracion: que herramienta llamo en el servidor y que le devolvio (sin la firma)
for s in interaction.steps:
    if s.type.startswith("mcp_server_tool"):
        print(f"[{s.type}]", str(s.model_dump(exclude={"signature"}))[:350])
print("\nRespuesta:", interaction.output_text)
