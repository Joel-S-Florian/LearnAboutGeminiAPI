# 06.6 Structured output + herramientas (preview)
# Se pueden combinar las dos cosas: el modelo USA herramientas (buscar en Google, leer URLs)
# y aun asi la respuesta FINAL llega con la forma de nuestro esquema.
#   - google_search: busca en Google (grounding) para datos actuales
#   - url_context:   lee el contenido de URLs que aparezcan en el prompt o la busqueda
# La doc lo marca como preview para Gemini 4 y Gemini 3 (incluye gemini-3.8-flash).

from typing import List

from google import genai
from pydantic import BaseModel, Field


class MatchResult(BaseModel):
    winner: str = Field(description="The name of the winner.")
    final_match_score: str = Field(description="The final match score.")
    scorers: List[str] = Field(description="The name of the scorer.")


# timeout en MILISEGUNDOS (aqui 2 min). Las llamadas anteriores de generacion se colgaron
# sin limite de tiempo. Comprobado: interactions SI lo respeta (lanza APITimeoutError al vencer)
client = genai.Client(http_options={"timeout": 120_000})

interaction = client.interactions.create(
    # La doc usa gemini-4-carbon, que no esta en la lista oficial de Joel; usamos gemini-3.8-flash
    model="gemini-3.8-flash",
    input="Search for all details for the latest Euro.",
    # tools: lista de herramientas; cada una es un dict con su "type"
    tools=[{"type": "google_search"}, {"type": "url_context"}],
    response_format={
        "type": "text",
        "mime_type": "application/json",
        "schema": MatchResult.model_json_schema(),
    },
)

# Aunque el modelo busque en la web, output_text sigue siendo el JSON final del esquema
result = MatchResult.model_validate_json(interaction.output_text)
print(result)
# Cuantos pasos (steps) hubo: ademas del texto final suele haber pasos de busqueda
print("Pasos en la interaccion:", [getattr(s, "type", None) for s in interaction.steps])
