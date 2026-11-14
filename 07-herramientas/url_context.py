# 07.3 url_context: el modelo LEE el contenido de las URLs que pongas en el prompt
# Util para extraer datos, comparar documentos o explicar codigo/docs de una pagina.
# Solo lee las URLs dadas (no sus enlaces internos) y deben ser publicas.

from google import genai

# Primero los modelos "lite" (limite gratis de 500 peticiones/dia segun rate_limit/*.json);
# los flash normales solo tienen 20/dia en el nivel gratuito
MODELOS = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.6-flash", "gemini-2.5-flash"]

# timeout en milisegundos (90 s)
client = genai.Client(http_options={"timeout": 90_000})

url1 = "https://www.foodnetwork.com/recipes/ina-garten/perfect-roast-chicken-recipe-1940592"
url2 = "https://www.allrecipes.com/recipe/21151/simple-whole-roast-chicken/"

interaction = None
for modelo in MODELOS:
    try:
        interaction = client.interactions.create(
            model=modelo,
            input=f"Compare the ingredients and cooking times from the recipes at {url1} and {url2}",
            tools=[{"type": "url_context"}],
        )
        print(f"Modelo usado: {modelo}\n")
        break
    except Exception as e:
        print(f"[{modelo}] fallo: {type(e).__name__} {getattr(e, 'status_code', None)}")

if interaction is None:
    raise SystemExit("Ningun modelo respondio.")

# Pasos: ademas del texto final hay un paso url_context_result (estado de cada URL; sirve para depurar)
print("Tipos de pasos:", [s.type for s in interaction.steps])

for step in interaction.steps:
    if step.type == "model_output":
        for content_block in step.content:
            if content_block.type == "text":
                print(content_block.text)
                # Citas: segmento del texto -> URL de origen
                if content_block.annotations:
                    print("\nFuentes:")
                    for annotation in content_block.annotations:
                        if annotation.type == "url_citation":
                            print(f" - {annotation.title}: {annotation.url}")
