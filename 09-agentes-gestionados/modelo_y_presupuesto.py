# 09.9 Modelo del agente y control de presupuesto, ambos dentro de agent_config:
#   "model":            que modelo Gemini usa el agente por dentro (por defecto gemini-4-hydrogen)
#   "max_total_tokens": tope de tokens (entrada + salida + razonamiento; los cacheados NO cuentan).
#                       Al alcanzarlo la interaccion para con status "incomplete" y conserva su trabajo.
# El tope es "best-effort": puede pasarse un poco, segun cuando el agente revise el presupuesto.
# Casos:
#   A) otro modelo (uno "lite", con mas cuota gratuita) y su costo
#   B) tope MUY bajo para provocar "incomplete"
#   C) continuar la interaccion incompleta con "continue" y un presupuesto nuevo

from google import genai

client = genai.Client(http_options={"api_version": "v1beta", "timeout": 300_000})
AGENTE = "antigravity-preview-09-2026"
TAREA = (
    "Write the first 20 Fibonacci numbers (starting 0, 1) to fibonacci.txt, one per line, "
    "then tell me their sum. Reply in one line."
)


def mostrar(titulo, r):
    tokens = r.usage.total_tokens if getattr(r, "usage", None) else "?"
    print(f"\n===== {titulo} =====")
    print((r.output_text or "(sin texto)").strip()[:300])
    print(f"-- estado={r.status} tokens={tokens} pasos={len(r.steps or [])}")


# A: modelo lite. La doc lista como opciones: gemini-4-hydrogen (defecto), gemini-4-carbon, gemini-4-argon,
# gemini-3.8-flash, gemini-3.6-flash, gemini-3.5-flash-lite
try:
    a = client.interactions.create(
        agent=AGENTE, input=TAREA, environment="remote",
        agent_config={"type": "antigravity", "model": "gemini-3.5-flash-lite", "max_total_tokens": 30_000},
    )
    mostrar("A: model=gemini-3.5-flash-lite", a)
except Exception as e:
    print(f"A fallo: {type(e).__name__} {getattr(e, 'status_code', None)} {str(e)[:300]}")

# B: tope diminuto
try:
    b = client.interactions.create(
        agent=AGENTE, input=TAREA, environment="remote",
        agent_config={"type": "antigravity", "model": "gemini-3.5-flash-lite", "max_total_tokens": 2_000},
    )
    mostrar("B: max_total_tokens=2000", b)
except Exception as e:
    raise SystemExit(f"B fallo: {type(e).__name__} {getattr(e, 'status_code', None)} {str(e)[:300]}")

# C: si B quedo incompleta, continuar: mismo previous_interaction_id y mismo entorno, presupuesto propio
if b.status == "incomplete":
    c = client.interactions.create(
        agent=AGENTE, input="continue", previous_interaction_id=b.id, environment=b.environment_id,
        agent_config={"type": "antigravity", "model": "gemini-3.5-flash-lite", "max_total_tokens": 30_000},
    )
    mostrar("C: continue (presupuesto nuevo)", c)
else:
    print("\nB no quedo incompleta: el tope no se alcanzo, no hay nada que continuar.")
