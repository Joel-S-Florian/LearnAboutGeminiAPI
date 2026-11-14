# 06.2 Structured output: extraer datos de un texto, con objetos anidados
# Diferencias con receta_basica.py:
#   - ahora el modelo NO inventa la receta: EXTRAE los datos de un texto que le damos
#   - el esquema tiene un objeto dentro de otro (Recipe contiene una lista de Ingredient)

from typing import List, Optional

from google import genai
from pydantic import BaseModel, Field


# Clase pequena para un ingrediente: nombre y cantidad (con unidades) por separado
class Ingredient(BaseModel):
    name: str = Field(description="Name of the ingredient.")
    quantity: str = Field(description="Quantity of the ingredient, including units.")


class Recipe(BaseModel):
    recipe_name: str = Field(description="The name of the recipe.")
    prep_time_minutes: Optional[int] = Field(description="Optional time in minutes to prepare the recipe.")
    # List[Ingredient]: una lista de OBJETOS (antes era una lista de str)
    ingredients: List[Ingredient]
    instructions: List[str]


client = genai.Client()

# Texto del que el modelo sacara los datos (viene de la documentacion)
prompt = """
Please extract the recipe from the following text.
The user wants to make delicious chocolate chip cookies.
They need 2 and 1/4 cups of all-purpose flour, 1 teaspoon of baking soda,
1 teaspoon of salt, 1 cup of unsalted butter (softened), 3/4 cup of granulated sugar,
3/4 cup of packed brown sugar, 1 teaspoon of vanilla extract, and 2 large eggs.
For the best part, they'll need 2 cups of semisweet chocolate chips.
First, preheat the oven to 375°F (190°C). Then, in a small bowl, whisk together the flour,
baking soda, and salt. In a large bowl, cream together the butter, granulated sugar, and brown sugar
until light and fluffy. Beat in the vanilla and eggs, one at a time. Gradually beat in the dry
ingredients until just combined. Finally, stir in the chocolate chips. Drop by rounded tablespoons
onto ungreased baking sheets and bake for 9 to 11 minutes.
"""

interaction = client.interactions.create(
    model="gemini-3.8-flash",
    input=prompt,
    # model_json_schema() incluye Ingredient dentro de Recipe automaticamente ($defs / $ref)
    response_format={
        "type": "text",
        "mime_type": "application/json",
        "schema": Recipe.model_json_schema(),
    },
)

recipe = Recipe.model_validate_json(interaction.output_text)
print(recipe.recipe_name, "| tiempo:", recipe.prep_time_minutes)
# Cada ingrediente es un objeto Ingredient con sus atributos, no un texto suelto
for ing in recipe.ingredients:
    print(f"  - {ing.quantity} | {ing.name}")
print("Pasos:", len(recipe.instructions))
