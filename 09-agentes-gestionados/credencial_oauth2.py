# 09.26 Credencial OAuth2: al CREARLA, la API hace un intercambio real del refresh_token contra token_url y solo la guarda si
# el proveedor devuelve un access_token. Sin un proveedor OAuth real con un refresh token valido NO se puede probar el EXITO;
# aqui se prueban los CAMINOS DE ERROR con valores FALSOS y httpbin.org como "proveedor" (se le envian solo datos falsos):
#   a) token_url que responde 403          b) token_url que responde 200 pero sin access_token
#   c) dominio que no existe               d) falta un campo obligatorio (client_secret)
#   e) token_url con http:// (sin TLS)     f) campo desconocido
# Si alguna se llegara a guardar, se borra en finally.

from google import genai

client = genai.Client(http_options={"api_version": "v1beta", "timeout": 90_000})
base = dict(type="oauth2", client_id="id-falso", client_secret="secreto-falso", refresh_token="rt-falso", scopes=["read"])
creadas = []


def intento(titulo, id, **cambios):
    try:
        c = client.credentials.create(id=id, **{**base, **cambios})
        creadas.append(id)
        print(f"[{titulo}] SE GUARDO: {c.id} {c.status}")
    except Exception as e:
        print(f"[{titulo}] fallo: {getattr(e, 'status_code', None)} {str(e)[:330]}")


try:
    intento("a token_url 403", "estudio-oa-a", token_url="https://httpbin.org/status/403")
    intento("b 200 sin access_token", "estudio-oa-b", token_url="https://httpbin.org/anything")
    intento("c dominio inexistente", "estudio-oa-c", token_url="https://no-existe-xyz-123.invalid/token")
    intento("d sin client_secret", "estudio-oa-d", token_url="https://httpbin.org/status/403", client_secret=None)
    intento("e http sin TLS", "estudio-oa-e", token_url="http://httpbin.org/status/403")
    intento("f campo desconocido", "estudio-oa-f", token_url="https://httpbin.org/status/403", clientSecret="x")
finally:
    for i in creadas:
        client.credentials.delete(id=i)
    print("quedan credenciales:", [x.id for x in client.credentials.list().credentials or []])
