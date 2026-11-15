# 11.4 Webhooks (solo la parte de API; NO hay servidor publico que reciba eventos, asi que no se prueba una entrega real).
# Todas las URLs apuntan a un dominio reservado `.invalid` (no existe): si el servicio llegara a entregar algo, falla sin enviar nada a nadie.
# Se prueba: (1) CRUD de webhooks estaticos (create / get / list / update / delete), (2) el secreto de firma (`new_signing_secret`, que se muestra UNA vez;
# NUNCA se imprime, solo su longitud y su prefijo) y su rotacion, (3) errores de validacion, (4) webhooks DINAMICOS (`webhook_config` en una interaccion
# en segundo plano), (5) un verificador de firma Standard Webhooks escrito a mano y comprobado contra una firma generada con el secreto real.
# Todo se borra al final. Ejecutar con `python -u ... > archivo`.

import base64
import hashlib
import hmac
import time

from google import genai

client = genai.Client(http_options={"api_version": "v1beta", "timeout": 40_000})
W = client.webhooks
URI = "https://example.invalid/gemini-callback"
creados = []


def err(e):
    return f"{getattr(e, 'status_code', None)} {type(e).__name__}: {str(e)[:260]}"


def intento(titulo, fn):
    try:
        r = fn()
        print(f"[{titulo}] OK")
        return r
    except Exception as e:
        print(f"[{titulo}] FALLO {err(e)}")


def campos(w):
    d = w.model_dump()
    return {k: (f"<{len(v)} caracteres, prefijo {v[:6]!r}>" if "secret" in k and isinstance(v, str) else v) for k, v in d.items() if v is not None}


try:
    print("=== 1) estado inicial y creacion ===")
    previos = intento("list", lambda: W.list())
    print("webhooks existentes:", [(x.id, x.name) for x in (previos.webhooks or [])] if previos is not None else "?")
    w = intento("create", lambda: W.create(name="estudio-webhook", subscribed_events=["batch.succeeded", "batch.failed"], uri=URI))
    secreto = None
    if w:
        creados.append(w.id)
        secreto = getattr(w, "new_signing_secret", None)
        print("   campos:", campos(w))

    print("\n=== 2) get / list / update ===")
    if w:
        g = intento("get", lambda: W.get(id=w.id))
        if g:
            print("   get (el secreto vuelve a verse?):", {k: v for k, v in campos(g).items() if "secret" in k} or "no, solo se muestra al crear")
        u = intento("update (anadir un evento)", lambda: W.update(id=w.id, subscribed_events=["batch.succeeded", "batch.failed", "batch.cancelled", "interaction.completed"]))
        if u:
            print("   eventos tras update:", u.subscribed_events)
        print("   list:", [(x.id[:8], x.name, x.subscribed_events) for x in (W.list().webhooks or [])])

    print("\n=== 3) rotar el secreto ===")
    if w:
        for comportamiento in ("revoke_previous_secrets_after_h24", "revoke_previous_secrets_immediately", "valor_falso"):
            r = intento(f"rotate ({comportamiento})", lambda c=comportamiento: W.rotate_signing_secret(id=w.id, revocation_behavior=c))
            if r:
                nuevo = getattr(r, "secret", None) or getattr(r, "new_signing_secret", None)
                print("   respuesta:", {k: (f"<{len(v)} caracteres>" if "secret" in k and isinstance(v, str) else v) for k, v in r.model_dump().items() if v is not None},
                      "| distinto del anterior:", nuevo != secreto)
                secreto = nuevo or secreto

    print("\n=== 4) errores de validacion ===")
    for titulo, kw in (("evento inexistente", dict(name="x1", subscribed_events=["foo.bar"], uri=URI)),
                       ("sin eventos", dict(name="x2", subscribed_events=[], uri=URI)),
                       ("uri http (sin TLS)", dict(name="x3", subscribed_events=["batch.succeeded"], uri="http://example.invalid/h")),
                       ("uri localhost", dict(name="x4", subscribed_events=["batch.succeeded"], uri="https://localhost:8000/h")),
                       ("uri no valida", dict(name="x5", subscribed_events=["batch.succeeded"], uri="no-es-una-url")),
                       ("nombre repetido", dict(name="estudio-webhook", subscribed_events=["batch.succeeded"], uri=URI))):
        r = intento(titulo, lambda kw=kw: W.create(**kw))
        if r:
            creados.append(r.id)
    intento("get inexistente", lambda: W.get(id="id-que-no-existe"))

    print("\n=== 5) webhooks DINAMICOS (webhook_config en una interaccion en segundo plano) ===")
    cfg = {"uris": [URI], "user_metadata": {"grupo": "estudio", "prioridad": "alta"}}
    i1 = intento("con background=True", lambda: client.interactions.create(model="gemini-3.5-flash-lite", input="Reply OK.", background=True, webhook_config=cfg))
    if i1:
        print("   id:", i1.id, "| estado inicial:", i1.status, "| campos con 'webhook':", {k: v for k, v in i1.model_dump().items() if "webhook" in k and v is not None})
        for _ in range(10):
            if i1.status not in ("in_progress", "queued"):
                break
            time.sleep(3)
            i1 = client.interactions.get(id=i1.id)
        print("   estado final:", i1.status, "| texto:", (i1.output_text or "")[:20])
        client.interactions.delete(id=i1.id)
    intento("SIN background", lambda: client.interactions.create(model="gemini-3.5-flash-lite", input="Reply OK.", webhook_config=cfg))
    intento("uri http", lambda: client.interactions.create(model="gemini-3.5-flash-lite", input="Reply OK.", background=True, webhook_config={"uris": ["http://example.invalid/h"]}))
    intento("sin uris", lambda: client.interactions.create(model="gemini-3.5-flash-lite", input="Reply OK.", background=True, webhook_config={"user_metadata": {"a": "b"}}))

    print("\n=== 6) verificador de firma Standard Webhooks (a mano) ===")
    if secreto:
        print("   formato del secreto: prefijo", repr(secreto[:6]), "| longitud", len(secreto))
        clave_b64 = secreto.split("_", 1)[1] if secreto.startswith("whsec_") else secreto
        try:
            clave = base64.b64decode(clave_b64)
            print("   decodifica como base64:", len(clave), "bytes")
        except Exception as e:
            clave = secreto.encode()
            print("   NO es base64 valido; se usa el texto tal cual:", type(e).__name__)

        def firmar(msg_id, ts, cuerpo):
            return "v1," + base64.b64encode(hmac.new(clave, f"{msg_id}.{ts}.{cuerpo}".encode(), hashlib.sha256).digest()).decode()

        def verificar(cabeceras, cuerpo, tolerancia=300):
            ts = int(cabeceras["webhook-timestamp"])
            if abs(time.time() - ts) > tolerancia:
                return "RECHAZADO: marca de tiempo fuera de 5 min (anti-repeticion)"
            esperada = firmar(cabeceras["webhook-id"], ts, cuerpo)
            for f in cabeceras["webhook-signature"].split(" "):
                if hmac.compare_digest(f, esperada):
                    return "VALIDO"
            return "RECHAZADO: firma invalida"

        cuerpo = '{"type":"batch.succeeded","version":"v1","timestamp":"2026-11-14T12:00:00Z","data":{"id":"batch_123456"}}'
        ahora = int(time.time())
        ok = {"webhook-id": "msg_1", "webhook-timestamp": str(ahora), "webhook-signature": firmar("msg_1", ahora, cuerpo)}
        print("   firma correcta            ->", verificar(ok, cuerpo))
        print("   cuerpo alterado           ->", verificar(ok, cuerpo.replace("123456", "999999")))
        viejo = {**ok, "webhook-timestamp": str(ahora - 3600), "webhook-signature": firmar("msg_1", ahora - 3600, cuerpo)}
        print("   mensaje de hace 1 hora    ->", verificar(viejo, cuerpo))
        print("   (el cuerpo debe verificarse CRUDO: re-serializar el JSON cambia los bytes y rompe la firma)")
finally:
    for wid in set(creados):
        try:
            W.delete(id=wid)
        except Exception:
            pass
    print("\nwebhooks que quedan:", [(x.id[:8], x.name) for x in (W.list().webhooks or [])])
