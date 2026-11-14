# 04.6 TTS: voces - biblioteca extendida (client.voices.list)
# Ademas de las 30 voces predefinidas, hay cientos mas en la "Voice Library".
# voices.list() SOLO CONSULTA: no crea nada en tu proyecto (a diferencia de diseno,
# remix o replica de voces, que si guardan recursos).

from google import genai

client = genai.Client(http_options={"api_version": "v1beta"})

# Los filtros de tipo lista se combinan asi: dentro de un filtro, "O" (cualquiera de los valores);
# entre filtros distintos, "Y" (todos deben cumplirse)
response = client.voices.list(
    language_code=["es-DO", "es-MX", "es-US", "es-ES"],  # codigos BCP-47 de idioma-region
    page_size=50,  # maximo de voces por pagina (por defecto 50, maximo 1000)
)

voces = response.voices or []
print(f"Voces recibidas: {len(voces)}")
for voice in voces:
    print(
        f"{voice.id} | {voice.display_name} ({voice.language_code}, {voice.accent}, "
        f"{voice.gender}, pitch={voice.pitch}): {voice.description}"
    )

# Si hay mas paginas, response.next_page_token trae el token para pedir la siguiente
print("Hay mas paginas:", bool(response.next_page_token))
