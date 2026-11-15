# Ayuda de niveles_servicio.py: UN caso por proceso (para poder cortarlo si se cuelga). Uso: python _un_caso_tier.py MODELO TIER [code]
import sys
import time

from google import genai

modelo, tier = sys.argv[1], (None if sys.argv[2] == "none" else sys.argv[2])
code = len(sys.argv) > 3 and sys.argv[3] == "code"
c = genai.Client(http_options={"api_version": "v1beta", "timeout": 40_000})
kw = {"service_tier": tier} if tier else {}
if code:
    kw["tools"] = [{"type": "code_execution"}]
t0 = time.time()
try:
    resp = c.interactions.with_raw_response.create(
        model=modelo, input=("Use code execution to compute 123 * 456; reply with just the number." if code else "Reply with the single word OK."), **kw)
    r = resp.parse()
    print(f"{modelo:24} tier={str(tier):9} -> servido={getattr(r, 'service_tier', None)} | {time.time() - t0:.1f} s | tokens={r.usage.total_tokens} | {(r.output_text or '')[:12]!r}")
except Exception as e:
    print(f"{modelo:24} tier={str(tier):9} -> {getattr(e, 'status_code', None)} {type(e).__name__}: {str(e)[:200]} ({time.time() - t0:.1f} s)")
