# 08.3 Function calling para "ampliar capacidades": el modelo extrae DATOS tipados del texto
# y tu funcion (aqui solo la declaracion) fabricaria el grafico. Una sola ida, sin ejecutar nada.
# Fijate en los tipos del esquema: labels = lista de strings, values = lista de NUMEROS.

from pathlib import Path

from google import genai

# Carpeta de salidas junto a la raiz del repo (ignorada por git)
SALIDAS = Path(__file__).resolve().parent.parent / "salidas"

MODELOS = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-2.5-flash-lite"]

client = genai.Client(http_options={"timeout": 60_000})

create_chart_function = {
    "type": "function",
    "name": "create_bar_chart",
    "description": "Creates a bar chart given a title, labels, and values.",
    "parameters": {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "The title for the chart."},
            "labels": {"type": "array", "items": {"type": "string"}},
            # items "number": el modelo debe devolver 50000, no "50000"
            "values": {"type": "array", "items": {"type": "number"}},
        },
        "required": ["title", "labels", "values"],
    },
}

interaction = None
for modelo in MODELOS:
    try:
        interaction = client.interactions.create(
            model=modelo,
            input="Create a bar chart titled 'Quarterly Sales' with Q1: 50000, Q2: 75000, Q3: 60000.",
            tools=[create_chart_function],
        )
        print(f"Modelo usado: {modelo}\n")
        break
    except Exception as e:
        print(f"[{modelo}] fallo: {type(e).__name__} {getattr(e, 'status_code', None)}")

if interaction is None:
    raise SystemExit("Ningun modelo respondio.")


# TU funcion real: dibuja el grafico con matplotlib y lo guarda en salidas/ (requiere pip install matplotlib)
def create_bar_chart(title, labels, values):
    import matplotlib

    matplotlib.use("Agg")  # sin ventana: solo guardar el archivo
    import matplotlib.pyplot as plt

    SALIDAS.mkdir(exist_ok=True)
    plt.figure(figsize=(6, 4))
    plt.bar(labels, values, color="#4c78a8")
    plt.title(title)
    plt.tight_layout()
    ruta = SALIDAS / "grafico.png"
    plt.savefig(ruta)
    plt.close()
    return str(ruta)


for step in interaction.steps:
    if step.type == "function_call":
        print(f"Function to call: {step.name}")
        print(f"Arguments: {step.arguments}")
        # Comprobar los tipos reales de lo recibido
        print("Tipo de values[0]:", type(step.arguments["values"][0]).__name__)
        # Paso 3 del flujo: ejecutar localmente con los argumentos que pidio el modelo
        ruta = create_bar_chart(**step.arguments)
        print("Grafico guardado en:", ruta)
