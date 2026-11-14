# 06.8 Salida estructurada + url_context (no google_search): la busqueda en 3.x tiene cuota 0/0 gratis,
# pero url_context puede funcionar. Prueba si el esquema + una herramienta funciona en modelos 3.x.

from pydantic import BaseModel, Field

from google import genai


class Pagina(BaseModel):
    titulo: str = Field(description="Titulo principal de la pagina")
    tema: str = Field(description="De que trata, en una frase")


client = genai.Client(http_options={"api_version": "v1beta", "timeout": 120_000})
MODELOS = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.8-flash"]

for modelo in MODELOS:
    try:
        r = client.interactions.create(
            model=modelo,
            input="Lee https://example.com y dame su titulo y de que trata.",
            tools=[{"type": "url_context"}],
            response_format={"type": "text", "mime_type": "application/json", "schema": Pagina.model_json_schema()},
        )
    except Exception as e:
        print(f"[{modelo}] fallo: {type(e).__name__} {getattr(e, 'status_code', None)} {str(e)[:160]}")
        continue
    print(f"[{modelo}] OK, pasos:", [getattr(s, "type", None) for s in r.steps or []])
    print("  ", Pagina.model_validate_json(r.output_text))
    break
