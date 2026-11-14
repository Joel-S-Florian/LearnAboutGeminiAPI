# 06.7 Salida estructurada + google_search, reprobado con v1beta y modelos con respaldo.
# Antes (herramientas.py) no se pudo verificar por cuota. Aqui se prueba cada modelo y se anota
# que paso con cada uno (la combinacion esquema+herramientas es "preview" segun la doc).

from typing import List

from google import genai
from pydantic import BaseModel, Field


class MatchResult(BaseModel):
    winner: str = Field(description="The name of the winner.")
    final_match_score: str = Field(description="The final match score.")
    scorers: List[str] = Field(description="The name of the scorer.")


client = genai.Client(http_options={"api_version": "v1beta", "timeout": 120_000})
MODELOS = ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.8-flash"]

for modelo in MODELOS:
    try:
        r = client.interactions.create(
            model=modelo,
            input="Search for the final result of the most recent UEFA Euro men's final.",
            tools=[{"type": "google_search"}],
            response_format={"type": "text", "mime_type": "application/json", "schema": MatchResult.model_json_schema()},
        )
    except Exception as e:
        print(f"[{modelo}] fallo: {type(e).__name__} {getattr(e, 'status_code', None)} {str(e)[:200]}")
        continue
    print(f"[{modelo}] OK, pasos:", [getattr(s, "type", None) for s in r.steps or []])
    try:
        print("  validado:", MatchResult.model_validate_json(r.output_text))
    except Exception as e:
        print("  NO valida contra el esquema:", type(e).__name__, str(r.output_text)[:200])
    break
