# 06.5 Structured output con streaming
# Con stream=True el JSON llega en trozos mientras se genera. Cada trozo es un fragmento
# de texto JSON (parcial, no valido por si solo); al concatenarlos todos se obtiene el
# JSON completo, que ya podemos validar con Pydantic.

from typing import Literal

from google import genai
from pydantic import BaseModel


class Feedback(BaseModel):
    # Literal -> enum: solo uno de estos tres valores
    sentiment: Literal["positive", "neutral", "negative"]
    summary: str


client = genai.Client()
prompt = "The new UI is incredibly intuitive. Add a very long summary to test streaming!"

stream = client.interactions.create(
    model="gemini-3.8-flash",
    input=prompt,
    response_format={
        "type": "text",
        "mime_type": "application/json",
        "schema": Feedback.model_json_schema(),
    },
    stream=True,  # devuelve un iterador de eventos en vez de la respuesta completa
)

trozos = []
for event in stream:
    # Los eventos "step.delta" con delta de tipo "text" traen un fragmento del JSON.
    # Hay que filtrar por TIPO: antes del texto llega un delta "thought_signature" (bloque
    # interno del modelo) que no tiene el atributo .text y daria AttributeError
    if event.event_type == "step.delta" and event.delta.type == "text":
        trozos.append(event.delta.text)
        print(event.delta.text, end="", flush=True)  # se ve como va llegando

print(f"\n\nTrozos recibidos: {len(trozos)}")

# Solo AL FINAL, con el JSON completo, se puede validar (un trozo suelto no es JSON valido)
feedback = Feedback.model_validate_json("".join(trozos))
print("Validado:", feedback)
