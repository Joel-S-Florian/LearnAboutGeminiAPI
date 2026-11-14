# 07.6 computer_use: el modelo "ve" capturas de pantalla y PIDE acciones de interfaz (clic, teclear...)
# IMPORTANTE: el modelo NO ejecuta nada. Devuelve un paso "function_call" (p. ej. click con x, y)
# y TU codigo debe ejecutarlo (con Playwright, por ejemplo) y devolverle una captura nueva.
# Este script es solo el primer paso: ver que accion propone, sin ejecutar nada.
# La doc recomienda un entorno aislado (VM/contenedor) cuando se ejecuta de verdad.

from google import genai

# Modelos que la doc lista para computer use (3.8 Flash, 3.5 Flash-Lite, 3 Flash Preview)
MODELOS = ["gemini-3.5-flash-lite", "gemini-3.8-flash", "gemini-3-flash-preview"]

client = genai.Client(http_options={"timeout": 60_000})

interaction = None
for modelo in MODELOS:
    try:
        interaction = client.interactions.create(
            model=modelo,
            input="Search for 'Gemini API' on Google.",
            # environment: "browser", "mobile" o "desktop" (cambia el conjunto de acciones)
            tools=[{"type": "computer_use", "environment": "browser"}],
        )
        print(f"Modelo usado: {modelo}\n")
        break
    except Exception as e:
        print(f"[{modelo}] fallo: {type(e).__name__} {getattr(e, 'status_code', None)} {str(e)[:200]}")

if interaction is None:
    raise SystemExit("Ningun modelo respondio.")

print("Tipos de pasos:", [s.type for s in interaction.steps])
for step in interaction.steps:
    if step.type == "function_call":
        # name = accion (click, type, navigate...); arguments trae coordenadas 0-999 e "intent"
        print("Accion propuesta:", step.name, step.arguments)
    elif step.type == "model_output":
        for bloque in step.content:
            if bloque.type == "text":
                print("[texto]", bloque.text)
