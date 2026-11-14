# 07.2 code_execution: el modelo escribe y EJECUTA Python en los servidores de Google
# Solo ejecuta Python (puede escribir otros lenguajes, pero no correrlos).
# Los pasos de la interaccion distinguen tres cosas: texto, codigo generado y resultado.

from google import genai

# Lista de modelos: si uno falla (503, timeout, cuota), se prueba el siguiente.
# Comprobado el 2026-11-14: gemini-3.8-flash dio 503 y gemini-3.1-flash-lite timeout,
# mientras 3.6-flash, 3.5-flash-lite y 2.5-flash respondieron bien.
MODELOS = ["gemini-3.6-flash", "gemini-3.5-flash-lite", "gemini-2.5-flash", "gemini-3.8-flash"]

# timeout en milisegundos (60 s) por si la llamada se cuelga
client = genai.Client(http_options={"timeout": 60_000})

interaction = None
for modelo in MODELOS:
    try:
        interaction = client.interactions.create(
            model=modelo,
            input="What is the sum of the first 50 prime numbers? "
            "Generate and run code for the calculation, and make sure you get all 50.",
            tools=[{"type": "code_execution"}],
        )
        print(f"Modelo usado: {modelo}\n")
        break
    except Exception as e:
        print(f"[{modelo}] fallo: {type(e).__name__} {getattr(e, 'status_code', None)}")

if interaction is None:
    raise SystemExit("Ningun modelo respondio.")

for step in interaction.steps:
    if step.type == "model_output":  # texto del modelo
        for content_block in step.content:
            if content_block.type == "text":
                print("[texto]", content_block.text)
    elif step.type == "code_execution_call":  # codigo que el modelo escribio
        print("[codigo]\n", step.arguments.code)
    elif step.type == "code_execution_result":  # lo que imprimio al ejecutarse
        print("[resultado]", step.result)
