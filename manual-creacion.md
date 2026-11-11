# Hacer una llamada a la API de GEMINI
# 1. Get an Gemini API Key
```
export GEMINI_API_KEY = "api-key-here!"
```

# 2. Install Google SDK
```
pip install -U google-genai
```
O en CMD:
```
set GEMINI_API_KEY=tu_clave_real_aqui
```
# 3. Start to develop the code
## Create script.py for import libraries and create an client object 
```
from google import genai 
```
## SDK  buscara automaticamente la variable de entorno GEMINI_API_KEY, no puede tener otro nombre
```
client = genai.Client() 
```

### ¿Que hace genai.Client() internamente?
1. Busca la API Key en las variables de entorno GEMINI_API_KEY o GOOGLE_API_KEY. Si no la encuentra, la creación del cliente puede fallar o las llamadas posteriores serán rechazadas.
2. Crea un objeto Python que almacena internamente esa clave y la configuración de conexión.
3. Prepara los métodos que usarás después, como client.models.generate_content(...).

## Creamos una variable para la pregunta
```
pregunta = "¿Porque el cielo es azul?"
```

## Creamos el objeto para recibir la respuesta
```
respuesta = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=pregunta
)
```
### Aqui un diagrama de Mermaid para entenderlo mejor
```
sequenceDiagram
    participant Tú as Tu código Python
    participant SDK as SDK google-genai
    participant API as API de Gemini
    Tú->>SDK: client.models.generate_content(model, contents)
    SDK->>API: Petición HTTP (con tu API Key)
    API-->>SDK: Respuesta en JSON
    SDK-->>Tú: Objeto de respuesta de Python
```

## Imprimir la respuesta
```
print(respuesta.text)
```
