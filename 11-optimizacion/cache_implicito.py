# 11.1 Caché de contexto IMPLICITO. La doc: en la Interactions API solo hay cache implicito (el explicito no esta soportado); se activa solo en
# Gemini 2.5 y posteriores cuando el prefijo repetido supera un minimo (4 096 tokens en 3.8 Flash / 3.6 Flash / 3.1 Pro / Gemini 4; 2 048 en 2.5 Flash
# y 2.5 Pro); para aumentar los aciertos: poner el contenido grande y comun AL PRINCIPIO y mandar peticiones con el mismo prefijo en poco tiempo. Los
# tokens servidos desde cache salen en `usage.total_cached_tokens`.
# Se prueba: (A) misma base grande, preguntas distintas, seguidas y tras 45 s; (B) cambiar la PRIMERA linea del prefijo; (C) prefijo pequeno (< minimo);
# (D) conversacion con estado (previous_interaction_id). Cada modelo con su propia base (para que un modelo no caliente la cache del otro).
# Ejecutar con `python -u ... > archivo`.

import random
import sys
import time

from google import genai

client = genai.Client(http_options={"api_version": "v1beta", "timeout": 120_000})


def base(n_entradas, semilla):
    """Texto grande y DETERMINISTA: n_entradas lineas distintas (~35 tokens cada una)."""
    r = random.Random(semilla)
    lineas = [f"Registro {i:04d}: la estacion {r.choice(['Alfa', 'Beta', 'Gamma', 'Delta', 'Sigma'])}-{r.randint(100, 999)} midio {r.randint(1000, 9999)} unidades "
              f"de {r.choice(['presion', 'caudal', 'voltaje', 'humedad'])} el dia {r.randint(1, 28)} del mes {r.randint(1, 12)} con el codigo {r.randint(10**6, 10**7 - 1)}."
              for i in range(n_entradas)]
    return "\n".join(lineas)


def pregunta(modelo, prefijo, q, **kw):
    t0 = time.time()
    try:
        r = client.interactions.create(model=modelo, input=prefijo + "\n\nPREGUNTA: " + q + " Responde en una frase corta.", **kw)
    except Exception as e:
        print(f"      FALLO {type(e).__name__} {getattr(e, 'status_code', None)} {str(e)[:200]}")
        return None
    u = r.usage
    ent, cach = getattr(u, "total_input_tokens", None), getattr(u, "total_cached_tokens", None)
    print(f"      entrada={ent} | en cache={cach} ({(100 * cach / ent):.0f} %) | salida={getattr(u, 'total_output_tokens', None)} | {time.time() - t0:.1f} s | {(r.output_text or '')[:60]!r}")
    return r


def probar(modelo, n_entradas, semilla, completo=True):
    print(f"\n########## {modelo} (base de {n_entradas} registros) ##########")
    P = base(n_entradas, semilla)
    print("  A) misma base, preguntas distintas:")
    r1 = pregunta(modelo, P, "Cual es el codigo del Registro 0007?")
    pregunta(modelo, P, "Cual es el codigo del Registro 0012?")
    if completo:
        print("     (espero 45 s)")
        time.sleep(45)
        pregunta(modelo, P, "Cual es el codigo del Registro 0020?")
        print("  B) cambiando la PRIMERA linea del prefijo:")
        pregunta(modelo, "NOTA DE LA VERSION 2.\n" + P, "Cual es el codigo del Registro 0007?")
        print("  C) prefijo PEQUENO (~15 registros, bajo el minimo):")
        chica = base(15, semilla + 1)
        pregunta(modelo, chica, "Cual es el codigo del Registro 0003?")
        pregunta(modelo, chica, "Cual es el codigo del Registro 0004?")
        if r1 is not None:
            print("  D) con estado (previous_interaction_id sobre la primera llamada):")
            pregunta(modelo, "", "Y el del Registro 0030?", previous_interaction_id=r1.id) if False else None
            try:
                t0 = time.time()
                r = client.interactions.create(model=modelo, previous_interaction_id=r1.id, input="Ahora dime el codigo del Registro 0030, en una frase corta.")
                u = r.usage
                print(f"      entrada={u.total_input_tokens} | en cache={u.total_cached_tokens} | {time.time() - t0:.1f} s | {(r.output_text or '')[:60]!r}")
            except Exception as e:
                print(f"      FALLO {type(e).__name__} {getattr(e, 'status_code', None)} {str(e)[:200]}")


probar("gemini-3.5-flash-lite", 220, 11)
probar("gemini-2.5-flash", 220, 22)
probar("gemini-3.8-flash", 220, 33, completo=False)  # cuota de 20 peticiones al dia: solo 2 llamadas
