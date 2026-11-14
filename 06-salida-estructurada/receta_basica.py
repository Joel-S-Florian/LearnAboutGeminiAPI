# 06.1 Structured output: salida estructurada (receta basica)
# Le pedimos al modelo que responda con JSON que cumpla un ESQUEMA que definimos nosotros.
# Pydantic (libreria de Python) genera ese esquema a partir de una clase y despues
# valida la respuesta. Asi recibimos datos con tipos, no texto libre.

from typing import List, Optional

from google import genai
from pydantic import BaseModel, Field


# El esquema es una clase: cada atributo es un campo del JSON, con su tipo.
# Field(description=...) le explica al modelo que va en cada campo (guia la respuesta).
class Recipe(BaseModel):
    recipe_name: str = Field(description="Name of the recipe.")
    ingredients: List[str] = Field(description="List of ingredients.")
    # Optional[int] = puede ser entero o None (el campo puede faltar o ser null)
    prep_time_minutes: Optional[int] = Field(description="Prep time in minutes.")


client = genai.Client()

interaction = client.interactions.create(
    # La doc usa gemini-4-hydrogen, que no esta en la lista oficial; usamos gemini-3.8-flash
    model="gemini-3.8-flash",
    input="Give me a recipe for banana bread",
    # response_format: como queremos la salida.
    #   type "text" + mime_type "application/json" = texto que es JSON
    #   schema = el esquema JSON; Recipe.model_json_schema() lo genera desde la clase
    response_format={
        "type": "text",
        "mime_type": "application/json",
        "schema": Recipe.model_json_schema(),
    },
)

# output_text es un str con el JSON. model_validate_json lo convierte en un objeto Recipe
# y comprueba que cumple el esquema (si no cumple, lanza ValidationError)
recipe = Recipe.model_validate_json(interaction.output_text)
print(recipe)
# Ahora los campos son atributos tipados: recipe.ingredients es una lista real de str
print("Ingredientes:", len(recipe.ingredients), "| tiempo:", recipe.prep_time_minutes)
