# NOTA: esta version (todo en un proceso) se COLGO en la 4.a llamada (>9 min pese al timeout del cliente). Los resultados completos salieron de
# `_un_caso_tier.py`, que ejecuta UN caso por proceso y se corta con `timeout 70` del sistema (ver BITACORA).
# 11.2 Niveles de servicio sincronos: `service_tier` = "standard" (defecto) | "flex" (50 % menos, hasta 15 min, "sheddable", puede dar 503/429 y NO hay
# fallback automatico) | "priority" (75-100 % mas, maxima prioridad, si se superan los limites dinamicos BAJA a standard y se cobra como standard;
# la doc dice que se vigile la cabecera `x-gemini-service-tier`). Se mira: si el nivel gratuito los acepta, que nivel DECLARA la respuesta
# (`r.service_tier`), si aparece la cabecera, la latencia de cada nivel, valores invalidos y combinaciones (herramienta, historial).
# Timeouts cortos (la doc recomienda 10 min+ para Flex en cargas reales; aqui las peticiones son diminutas). Ejecutar con `python -u ... > archivo`.

import time

from google import genai

client = genai.Client(http_options={"api_version": "v1beta", "timeout": 45_000})
RAW = client.interactions.with_raw_response
cabeceras_vistas = {}


def llamar(modelo, tier, input="Reply with the single word OK.", **kw):
    t0 = time.time()
    extra = {"service_tier": tier} if tier is not None else {}
    try:
        resp = RAW.create(model=modelo, input=input, **extra, **kw)
    except Exception as e:
        return {"error": f"{getattr(e, 'status_code', None)} {type(e).__name__}: {str(e)[:210]}", "s": time.time() - t0}
    r = resp.parse()
    cabeceras_vistas.update({k.lower(): v for k, v in dict(resp.headers).items() if "tier" in k.lower() or "gemini" in k.lower() or "service" in k.lower()})
    return {"tier_pedido": tier, "tier_servido": getattr(r, "service_tier", None), "tokens": getattr(r.usage, "total_tokens", None), "s": time.time() - t0,
            "texto": (r.output_text or "")[:20]}


print("=== 1) cada nivel en cada modelo ===")
for modelo in ("gemini-3.5-flash-lite", "gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-3.1-flash-lite"):
    print(f"\n[{modelo}]")
    for tier in (None, "standard", "flex", "priority"):
        r = llamar(modelo, tier)
        if "error" in r:
            print(f"   tier={str(tier):9} -> {r['error']} ({r['s']:.1f} s)")
        else:
            print(f"   tier={str(tier):9} -> servido={r['tier_servido']} | {r['s']:.1f} s | tokens={r['tokens']} | {r['texto']!r}")

print("\n=== 2) valor invalido ===")
print("  ", llamar("gemini-3.5-flash-lite", "turbo"))

print("\n=== 3) latencia: 4 muestras por nivel (gemini-3.5-flash-lite) ===")
for tier in ("standard", "flex", "priority"):
    tiempos = []
    for _ in range(4):
        r = llamar("gemini-3.5-flash-lite", tier)
        tiempos.append(r["s"] if "error" not in r else None)
    ok = [t for t in tiempos if t is not None]
    print(f"   {tier:9}: {[round(t, 1) if t else 'ERR' for t in tiempos]} | media={sum(ok) / len(ok):.1f} s" if ok else f"   {tier:9}: todas fallaron")

print("\n=== 4) combinaciones con flex ===")
r = llamar("gemini-3.5-flash-lite", "flex", input="Use code execution to compute 123 * 456 and reply with just the number.", tools=[{"type": "code_execution"}])
print("   flex + code_execution:", r)
r1 = llamar("gemini-3.5-flash-lite", "flex", input="Remember the number 7.")
print("   flex turno 1:", r1)

print("\n=== 5) cabeceras de la respuesta que mencionan tier/gemini/service ===")
print("  ", cabeceras_vistas or "(ninguna)")
