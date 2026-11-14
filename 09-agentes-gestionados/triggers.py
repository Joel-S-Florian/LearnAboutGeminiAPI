# 09.21 Triggers: programan un agente con una expresion cron. Un trigger une agente + entorno + prompt + horario en un
# recurso persistente que se dispara SOLO, sin supervision (y gasta tokens cada vez). Todas las ejecuciones
# reutilizan el MISMO entorno, asi que los archivos persisten entre ejecuciones.
# Precauciones de este script (es un recurso que puede gastar dinero sin que estes mirando):
#   - el horario es "0 3 1 1 *" (1 de enero a las 03:00 UTC): no se dispara en meses
#   - se PAUSA nada mas crearlo
#   - se ejecuta UNA vez a mano (triggers.run, funciona aunque este pausado) con una tarea trivial
#   - se BORRA al final (try/finally), pase lo que pase
# Metodos: create, get, list, update(status=paused|active), run, list_executions, delete.

import time

from google import genai

client = genai.Client(http_options={"api_version": "v1beta", "timeout": 300_000})
trigger_id = None

try:
    trigger = client.triggers.create(
        schedule="0 3 1 1 *",
        time_zone="UTC",
        display_name="estudio-trigger",
        interaction={
            "agent": "antigravity-preview-09-2026",
            "input": "Reply with the single word OK. Do not use any tool.",
            "environment": "remote",
            "agent_config": {"type": "antigravity", "model": "gemini-3.5-flash-lite", "max_total_tokens": 10_000},
        },
    )
    trigger_id = trigger.id
    print(f"Creado: {trigger.id} estado={trigger.status} proxima ejecucion={trigger.next_run_time}")

    client.triggers.update(id=trigger_id, status="paused")
    t = client.triggers.get(id=trigger_id)
    print(f"Tras pausar: estado={t.status} horario={t.schedule}")
    print("list ->", [(x.id, x.display_name, x.status) for x in client.triggers.list().triggers or []])

    # Ejecutar ahora, a mano (no espera al horario y funciona estando pausado)
    client.triggers.run(trigger_id=trigger_id)
    print("run() enviado; esperando la ejecucion...")
    for _ in range(24):  # hasta ~2 min
        time.sleep(5)
        ejecuciones = client.triggers.list_executions(trigger_id=trigger_id).trigger_executions or []
        if ejecuciones and ejecuciones[0].status not in ("running", "in_progress", "RUNNING", "pending"):
            break
    for ex in ejecuciones:
        print(f"ejecucion {ex.id}: estado={ex.status} ({ex.start_time} -> {ex.end_time}) entorno={getattr(ex, 'environment_id', None)}")
        if getattr(ex, "interaction_id", None):
            r = client.interactions.get(id=ex.interaction_id)
            tokens = r.usage.total_tokens if getattr(r, "usage", None) else "?"
            print(f"  salida: {(r.output_text or '').strip()[:100]!r} tokens={tokens}")
finally:
    if trigger_id:
        try:
            client.triggers.delete(id=trigger_id)
            print("Borrado:", trigger_id)
        except Exception as e:
            print(f"NO SE PUDO BORRAR {trigger_id}: {type(e).__name__} {str(e)[:150]} -> borralo a mano")
        try:
            print("list tras borrar ->", [x.id for x in client.triggers.list().triggers or []])
        except Exception as e:
            print(f"list fallo: {type(e).__name__} {str(e)[:120]}")
