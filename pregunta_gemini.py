from google import genai

# SDK  buscara automaticamente la variable de entorno GEMINI_API_KEY, no puede tener otro nombre
    # client es el nombre de la variable, podria ser cliente o mi cliente, Gemini
    # genai.Client() es una funcion del SDK, como no le pasamos argumento, utiliza GEMINI_API_KEY por defecto
    # si quisieramos pasarle un argumento explicito, podria hacer algo como ´´genai.Client(api_key="...")´´
    # esto ultimo no es necesario o no es seguro
cliente = genai.Client()

# ---

# creamos la variable ´´pregunta´´ con el valor de la pregunta que queremos hacer
pregunta = "¿Porque el cielo es azul?"

# creamos ´´respuesta´´ como un objeto para recibir la respuesta
    # ´´model´´ es un parametro requerido por la API, le asignamos como valor al nombre del modelo que queremos que nos responda
    # ´´contents´´ es el parametro que contiene la pregunta, puede ser una cadena de texto simple
respuesta = cliente.models.generate_content(
    model="gemini-2.5-flash",
    contents=pregunta
)

# Imprimimos la respuesta
print(respuesta.text)
