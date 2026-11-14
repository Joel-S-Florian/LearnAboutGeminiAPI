# 09.23 Credenciales (client.credentials): crear, get, list (paginacion), rotar (update), borrar y errores.
# Todo con valores FALSOS (nunca un secreto real) y sin usar al agente (gratis). Se borran al final (finally).
# Doc: los valores secretos son "write-only": ningun endpoint los devuelve.

from google import genai

client = genai.Client(http_options={"api_version": "v1beta", "timeout": 60_000})
C = client.credentials
ids = ["estudio-cred-a", "estudio-cred-b", "estudio-cred-c"]


def intento(titulo, fn):
    try:
        r = fn()
        print(f"[{titulo}] OK")
        return r
    except Exception as e:
        print(f"[{titulo}] fallo: {getattr(e, 'status_code', None)} {str(e)[:170]}")


def meta(c):
    return {k: v for k, v in c.model_dump().items() if v is not None}


try:
    # 1) crear
    c = intento("crear bearer_token", lambda: C.create(id=ids[0], type="bearer_token", token="token-falso-AAA"))
    if c: print("   respuesta:", meta(c), "| 'token-falso-AAA' en la respuesta?:", "token-falso-AAA" in str(c))
    for i in ids[1:]:
        intento(f"crear {i}", lambda i=i: C.create(id=i, type="bearer_token", token="token-falso-BBB"))

    # 2) get y list
    g = C.get(id=ids[0]); print("\nget:", meta(g), "| token visible?:", "token-falso" in str(g))
    p1 = C.list(page_size=2)
    print(f"list page_size=2: {len(p1.credentials)} credenciales, next_page_token: {'si' if p1.next_page_token else 'no'}")
    if p1.next_page_token:
        p2 = C.list(page_size=2, page_token=p1.next_page_token)
        print(f"   pagina 2: {[x.id for x in p2.credentials]}")

    # 3) rotar (update): type obligatorio; los campos omitidos conservan su valor
    u = intento("rotar token (update)", lambda: C.update(id=ids[0], type="bearer_token", token="token-falso-NUEVO"))
    if u: print("   create_time vs update_time:", u.create_time, "|", u.update_time)
    intento("cambiar el type en update", lambda: C.update(id=ids[0], type="environment_variable", value="x", injection_location="header"))

    # 4) errores
    intento("crear id repetido (espera 409)", lambda: C.create(id=ids[0], type="bearer_token", token="x"))
    intento("get inexistente (espera 404)", lambda: C.get(id="no-existe-xyz"))
    intento("campo camelCase (espera 400)", lambda: C.create(id="estudio-cred-d", type="bearer_token", token="x", headerName="X-Api"))
    intento("sin token (espera 400)", lambda: C.create(id="estudio-cred-e", type="bearer_token"))
    intento("type no soportado (espera 400)", lambda: C.create(id="estudio-cred-f", type="basic_auth", token="x"))
    intento("id con mayusculas y espacios", lambda: C.create(id="Mi Cred", type="bearer_token", token="x"))
    # 5) id generado: se omite id
    n = intento("crear SIN id (UUID)", lambda: C.create(type="bearer_token", token="token-falso-CCC"))
    if n:
        ids.append(n.id); print("   id generado:", n.id)
finally:
    for i in ids + ["estudio-cred-d", "estudio-cred-e", "estudio-cred-f", "Mi Cred"]:
        try: C.delete(id=i)
        except Exception: pass
    # borrar dos veces el mismo
    intento("borrar de nuevo (idempotente?)", lambda: C.delete(id=ids[0]))
    print("quedan:", [x.id for x in C.list().credentials or []])
