# 06.4 Structured output: estructuras recursivas (organigrama)
# Un esquema RECURSIVO es uno que se referencia a si mismo: un Employee tiene una lista
# de "reports", y cada uno de ellos es OTRO Employee, que a su vez tiene sus reports...
# Asi se representan arboles de profundidad no fija (organigramas, carpetas, comentarios).

from typing import List

from google import genai
from pydantic import BaseModel, Field


class Employee(BaseModel):
    """Represents an employee in an organization."""

    name: str
    employee_id: int
    # List["Employee"]: la comilla es necesaria porque la clase aun no esta terminada de definir.
    # default_factory=list hace que el campo NO sea obligatorio (por defecto, lista vacia).
    # Eso importa: la doc recomienda que la referencia recursiva sea opcional, para que el
    # esquema no se rechace por demasiado complejo (400 INVALID_ARGUMENT)
    reports: List["Employee"] = Field(
        default_factory=list,
        description="A list of employees reporting to this employee.",
    )


client = genai.Client()

prompt = """
Generate an organization chart for a small team.
The manager is Alice, who manages Bob and Charlie. Bob manages David.
"""

interaction = client.interactions.create(
    model="gemini-3.8-flash",
    input=prompt,
    # model_json_schema() escribe la recursion con "$defs" y "$ref" (la clase se apunta a si misma)
    response_format={
        "type": "text",
        "mime_type": "application/json",
        "schema": Employee.model_json_schema(),
    },
)

employee = Employee.model_validate_json(interaction.output_text)


# Recorrido recursivo del arbol para verlo con sangria (la funcion tambien se llama a si misma)
def imprimir(e: Employee, nivel: int = 0) -> None:
    print("  " * nivel + f"- {e.name} (id {e.employee_id})")
    for r in e.reports:
        imprimir(r, nivel + 1)


imprimir(employee)
