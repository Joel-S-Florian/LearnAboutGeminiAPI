# 07.5 google_maps: respuestas ancladas en datos de Google Maps (lugares, resenas, horarios)
# Opcional: latitude/longitude dentro de la herramienta para consultas "cerca de aqui".
# Solo soporta prompts en ingles (segun la doc). Viene desactivada por defecto.
# Si la muestras al usuario, la doc exige citar la fuente como "Google Maps" con su enlace.

from google import genai

MODELOS = ["gemini-2.5-flash", "gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.6-flash"]

# v1beta por si acaso: google_search lo exigia (no verificado para maps)
client = genai.Client(http_options={"api_version": "v1beta", "timeout": 60_000})

interaction = None
for modelo in MODELOS:
    try:
        interaction = client.interactions.create(
            model=modelo,
            input="What are the best Italian restaurants within a 15-minute walk from here?",
            # Coordenadas de ejemplo de la doc (Los Angeles centro)
            tools=[{"type": "google_maps", "latitude": 34.050481, "longitude": -118.248526}],
        )
        print(f"Modelo usado: {modelo}\n")
        break
    except Exception as e:
        print(f"[{modelo}] fallo: {type(e).__name__} {getattr(e, 'status_code', None)} {str(e)[:200]}")

if interaction is None:
    raise SystemExit("Ningun modelo respondio.")

print("Tipos de pasos:", [s.type for s in interaction.steps])
for step in interaction.steps:
    if step.type == "model_output":
        for bloque in step.content:
            if bloque.type == "text":
                print(bloque.text)
                # Citas de lugares: nombre + enlace a Google Maps
                for a in bloque.annotations or []:
                    if a.type == "place_citation":
                        print(f" - {a.name}: {a.url}")
