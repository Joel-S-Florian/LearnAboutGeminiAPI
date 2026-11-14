# 08.2 Function calling para "tomar acciones": el modelo convierte lenguaje natural en ARGUMENTOS
# estructurados. Aqui NO ejecutamos nada: solo vemos que argumentos propone (una sola ida).
# Fijate como el modelo reformatea la fecha/hora segun lo que dicen las descripciones del esquema.

from google import genai

MODELOS = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-2.5-flash-lite"]

client = genai.Client(http_options={"timeout": 60_000})

schedule_meeting_function = {
    "type": "function",
    "name": "schedule_meeting",
    "description": "Schedules a meeting with specified attendees at a given time and date.",
    "parameters": {
        "type": "object",
        "properties": {
            # array de strings: el modelo puede devolver varios asistentes
            "attendees": {"type": "array", "items": {"type": "string"}},
            # El formato de ejemplo en la descripcion guia como escribe el valor el modelo
            "date": {"type": "string", "description": "Date (e.g., '2024-07-29')"},
            "time": {"type": "string", "description": "Time (e.g., '15:00')"},
            "topic": {"type": "string", "description": "The meeting topic."},
        },
        # required: el modelo debe incluir estos campos
        "required": ["attendees", "date", "time", "topic"],
    },
}

interaction = None
for modelo in MODELOS:
    try:
        interaction = client.interactions.create(
            model=modelo,
            input="Schedule a meeting with Bob and Alice for 03/14/2025 at 10:00 AM about Q3 planning.",
            tools=[schedule_meeting_function],
        )
        print(f"Modelo usado: {modelo}\n")
        break
    except Exception as e:
        print(f"[{modelo}] fallo: {type(e).__name__} {getattr(e, 'status_code', None)}")

if interaction is None:
    raise SystemExit("Ningun modelo respondio.")

print("Tipos de pasos:", [s.type for s in interaction.steps])
for step in interaction.steps:
    if step.type == "function_call":
        print(f"Function to call: {step.name}")
        print(f"Arguments: {step.arguments}")
