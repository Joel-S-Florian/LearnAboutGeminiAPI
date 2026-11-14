# 07.1 Google Search como herramienta (grounding)
# El modelo decide buscar en Google, lee los resultados y responde con citas.
# tools es una lista de dicts; cada uno lleva su "type" (aqui "google_search").

from google import genai

# Si un modelo falla (503, timeout, 429), se prueba el siguiente (ver code_execution.py)
# gemini-2.5-flash primero: en rate_limit/*.json la busqueda de "Gemini 3 and newer" tiene
# limite 0/0 en el nivel gratuito, y la de "Gemini 2.5" tiene 1.5K/dia
MODELOS = ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-3.5-flash-lite", "gemini-3.6-flash"]

# google_search requiere api_version v1beta: con la version por defecto (v1) da 400
# "Search as tool is not enabled for api version v1" (mensaje real de la API).
# timeout en milisegundos (60 s): las llamadas anteriores sin limite llegaron a colgarse
client = genai.Client(http_options={"api_version": "v1beta", "timeout": 60_000})

interaction = None
for modelo in MODELOS:
    try:
        interaction = client.interactions.create(
            model=modelo,
            input="Who won the euro 2024?",
            tools=[{"type": "google_search"}],
        )
        print(f"Modelo usado: {modelo}\n")
        break
    except Exception as e:
        print(f"[{modelo}] fallo: {type(e).__name__} {getattr(e, 'status_code', None)}")

if interaction is None:
    raise SystemExit("Ningun modelo respondio.")

# output_text es el texto final (puede traer citas en linea)
print(interaction.output_text)

# interaction.steps es la historia: pasos de busqueda + el paso final "model_output"
print("\nTipos de pasos:", [s.type for s in interaction.steps])

# Las citas viven en content_block.annotations (solo en bloques de texto)
for step in interaction.steps:
    if step.type == "model_output":
        for content_block in step.content:
            if content_block.type == "text" and content_block.annotations:
                print("\nCitas:")
                for annotation in content_block.annotations:
                    if annotation.type == "url_citation":
                        print(f" [{annotation.title}]({annotation.url})")
