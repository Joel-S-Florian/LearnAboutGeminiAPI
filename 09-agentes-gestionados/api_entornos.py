# 09.19 API de entornos: client.environments.create / list / get / delete (y errores).
# Descubierto: create() SIN argumentos crea un entorno hospedado vacio, sin gastar tokens (mode="hosted" no existe).
# Se prueba: paginacion de list, get de un id inexistente, usar un entorno creado a mano en una interaccion,
# borrar dos veces, y usar un entorno ya borrado. Todo lo creado se borra en finally.

from google import genai

client = genai.Client(http_options={"api_version": "v1beta", "timeout": 300_000})
creados = []


def err(e):
    return f"{getattr(e, 'status_code', None)} {str(e)[:130]}"


try:
    # 1) crear tres entornos vacios (gratis)
    for _ in range(3):
        e = client.environments.create()
        creados.append(e.id)
        print("creado:", e.id[:8], "status:", e.status)

    # 2) paginacion: page_size=2 con 3 entornos
    p1 = client.environments.list(page_size=2)
    print(f"\npagina 1: {len(p1.environments)} entornos, next_page_token: {'si' if p1.next_page_token else 'no'}")
    if p1.next_page_token:
        p2 = client.environments.list(page_size=2, page_token=p1.next_page_token)
        print(f"pagina 2: {len(p2.environments)} entornos, next_page_token: {'si' if p2.next_page_token else 'no'}")

    # 3) get: uno real y uno inexistente
    g = client.environments.get(id=creados[0])
    print("\nget real:", {k: v for k, v in g.model_dump().items() if v is not None})
    try:
        client.environments.get(id="id-que-no-existe")
    except Exception as ex:
        print("get inexistente ->", err(ex))

    # 4) que trae un entorno recien creado?
    fs = client.environments.files.list(environment=creados[0], path="", recursive=True).files or []
    print("\narchivos de un entorno vacio recien creado:", [(f.path, f.type) for f in fs])

    # 5) usarlo en una interaccion (pocos tokens)
    r = client.interactions.create(
        agent="antigravity-preview-09-2026", agent_config={"type": "antigravity", "max_total_tokens": 40_000},
        input="Write the text 'hola' into /workspace/prueba.txt and reply 'ok'.", environment=creados[0],
    )
    print(f"\ninteraccion en entorno creado a mano: {r.status}, mismo id: {r.environment_id == creados[0]}, tokens: {getattr(r.usage, 'total_tokens', '?')}")
    print("get tras usarlo:", {k: v for k, v in client.environments.get(id=creados[0]).model_dump().items() if k in ("file_count", "size_bytes", "status")})
finally:
    # 6) borrar; borrar de nuevo el mismo; y usar uno borrado
    for i in list(creados):
        client.environments.delete(id=i)
    print("\nborrados:", len(creados))
    try:
        client.environments.delete(id=creados[0])
        print("borrar dos veces: ACEPTADO sin error")
    except Exception as ex:
        print("borrar dos veces ->", err(ex))
    try:
        client.interactions.create(agent="antigravity-preview-09-2026", input="Say OK.", environment=creados[0])
        print("usar entorno borrado: ACEPTADO")
    except Exception as ex:
        print("usar entorno borrado ->", err(ex))
    print("quedan:", [x.id[:8] for x in client.environments.list().environments or []])
