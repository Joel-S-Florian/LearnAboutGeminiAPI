# 04.7 TTS: buscar voces en espanol de LATINOAMERICA en la biblioteca (solo CONSULTA, no crea nada ni gasta cuota de TTS).
# En 04.6 filtramos por language_code es-DO/MX/US/ES y solo llegaron voces es-ES. Aqui miramos TODO el catalogo
# (paginando) para ver que codigos de idioma, regiones y acentos existen realmente, sin suponer nombres.

from collections import Counter

from google import genai

client = genai.Client(http_options={"api_version": "v1beta"})

# Traer el catalogo completo: page_size maximo 1000; si hay mas paginas, seguir con next_page_token
voces, token = [], None
while True:
    r = client.voices.list(page_size=1000, page_token=token) if token else client.voices.list(page_size=1000)
    voces += r.voices or []
    token = r.next_page_token
    if not token:
        break
print(f"Voces en el catalogo: {len(voces)}")

idiomas = Counter(v.language_code for v in voces)
print(f"Idiomas distintos: {len(idiomas)}")
espanol = {k: n for k, n in idiomas.items() if k and k.lower().startswith("es")}
print("Codigos de idioma que empiezan por 'es':", espanol)

# Voces cuyo codigo es es-* O cuyo acento/descripcion menciona espanol o latino
pistas = ("latin", "mexic", "colomb", "argent", "caribb", "domin", "spanish", "chile", "peru", "venez", "cuba")
candidatas = [
    v for v in voces
    if (v.language_code or "").lower().startswith("es")
    or any(p in f"{v.accent} {v.description} {v.region_code}".lower() for p in pistas)
]
print(f"\nVoces candidatas: {len(candidatas)}")
for v in candidatas[:40]:
    print(f"  {v.id} | {v.display_name} | {v.language_code} | region={v.region_code} | accent={v.accent} | {v.gender}")

print("\nRegiones de las voces es-*:", Counter(v.region_code for v in voces if (v.language_code or "").lower().startswith("es")))
print("Acentos de las voces es-*:", Counter(v.accent for v in voces if (v.language_code or "").lower().startswith("es")))
