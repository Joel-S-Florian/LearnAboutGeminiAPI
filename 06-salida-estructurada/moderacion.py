# 06.3 Structured output: moderacion de contenido (Union/anyOf y Literal/enum)
# Dos ideas nuevas:
#   - Literal[...]  -> "enum" en el esquema: el campo SOLO puede valer uno de esos textos
#   - Union[A, B]   -> "anyOf": la respuesta tiene la forma de A o la forma de B,
#                      segun el caso (aqui: contenido spam o no spam)

from typing import Literal, Union

from google import genai
from pydantic import BaseModel, Field


# Forma de la respuesta cuando el contenido ES spam
class SpamDetails(BaseModel):
    reason: str = Field(description="The reason why the content is considered spam.")
    # Literal: el modelo no puede inventar otro tipo; debe elegir uno de estos cuatro
    spam_type: Literal["phishing", "scam", "unsolicited promotion", "other"] = Field(
        description="The type of spam."
    )


# Forma de la respuesta cuando el contenido NO es spam (campos distintos)
class NotSpamDetails(BaseModel):
    summary: str = Field(description="A brief summary of the content.")
    is_safe: bool = Field(description="Whether the content is safe for all audiences.")


class ModerationResult(BaseModel):
    # El modelo decide cual de las dos formas devolver
    decision: Union[SpamDetails, NotSpamDetails]


client = genai.Client()

# Dos contenidos a moderar: el de la documentacion (spam) y uno normal, para ver la otra rama
contenidos = [
    "Congratulations! You've won a free cruise to the Bahamas. Click here to claim your prize: www.definitely-not-a-scam.com",
    "Hi team, the weekly meeting is moved to Thursday at 10am. Please bring your status updates.",
]

for contenido in contenidos:
    interaction = client.interactions.create(
        model="gemini-3.8-flash",
        input=f"Please moderate the following content and provide a decision.\nContent: '{contenido}'",
        response_format={
            "type": "text",
            "mime_type": "application/json",
            "schema": ModerationResult.model_json_schema(),
        },
    )
    result = ModerationResult.model_validate_json(interaction.output_text)
    # isinstance dice cual de las dos formas llego
    rama = "SPAM" if isinstance(result.decision, SpamDetails) else "NO SPAM"
    print(f"[{rama}] {result.decision}")
