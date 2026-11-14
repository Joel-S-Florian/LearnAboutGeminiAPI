# 08.14 Function calling + salida estructurada (modelos Gemini 3): el modelo llama a TU funcion y la
# respuesta FINAL llega con la forma de un esquema Pydantic (como en 06-salida-estructurada).
# La doc solo dice que se pueden combinar; el codigo es nuestro: tools + response_format en la misma peticion.

import json

from google import genai
from pydantic import BaseModel, Field

MODELOS = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite"]

client = genai.Client(http_options={"timeout": 60_000})


class Reporte(BaseModel):
    city: str = Field(description="City name.")
    temperature_c: float = Field(description="Temperature in Celsius.")
    advice: str = Field(description="One short sentence of clothing advice.")


weather_tool = {
    "type": "function",
    "name": "get_current_temperature",
    "description": "Gets the current temperature for a given location.",
    "parameters": {
        "type": "object",
        "properties": {"location": {"type": "string", "description": "The city name"}},
        "required": ["location"],
    },
}

# Mismo formato de response_format que en el tema 06
FORMATO = {"type": "text", "mime_type": "application/json", "schema": Reporte.model_json_schema()}

interaction = None
modelo_usado = None
for modelo in MODELOS:
    try:
        interaction = client.interactions.create(
            model=modelo,
            input="What is the temperature in London and what should I wear?",
            tools=[weather_tool],
            response_format=FORMATO,
        )
        modelo_usado = modelo
        print(f"Modelo usado: {modelo}")
        break
    except Exception as e:
        print(f"[{modelo}] fallo: {type(e).__name__} {getattr(e, 'status_code', None)} {str(e)[:150]}")
if interaction is None:
    raise SystemExit("Ningun modelo respondio.")

print("Turno 1 pasos:", [s.type for s in interaction.steps])
call = next(s for s in interaction.steps if s.type == "function_call")
print("El modelo pide:", call.name, call.arguments)

result = {"location": call.arguments["location"], "temperature": 9, "unit": "celsius"}

final = client.interactions.create(
    model=modelo_usado,
    previous_interaction_id=interaction.id,
    tools=[weather_tool],
    response_format=FORMATO,  # hay que repetirlo: la respuesta FINAL es la que debe cumplir el esquema
    input=[{
        "type": "function_result",
        "name": call.name,
        "call_id": call.id,
        "result": [{"type": "text", "text": json.dumps(result)}],
    }],
)

print("\nTurno 2 pasos:", [s.type for s in final.steps], "| estado:", getattr(final, "status", None))
print("Texto crudo:", repr(final.output_text))
# Validar contra el esquema: si no cumple, lanza ValidationError
reporte = Reporte.model_validate_json(final.output_text)
print("Validado:", reporte)
