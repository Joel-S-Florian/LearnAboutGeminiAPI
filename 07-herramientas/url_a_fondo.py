# 07.18 URL context a fondo (T4). La doc: comparar paginas, anotaciones `url_citation`, paso `url_context_result` (status, retrieved_url),
# conteo de tokens (`tool_use_input_tokens`), tipos soportados (texto, imagen PNG/JPEG/BMP/WEBP, PDF) y NO soportados (YouTube, audio/video,
# paywall, Google Docs), maximo 20 URLs por peticion, solo URLs publicas (nada de localhost ni redes privadas), y no sigue enlaces anidados.
# Se usan URLs estables y publicas (httpbin.org, example.com, w3.org, un video de YouTube solo como URL). Solo se LEE.
# Ejecutar con `python -u ... > archivo`.

import time

from google import genai

client = genai.Client(http_options={"api_version": "v1beta", "timeout": 120_000})
MODELO = "gemini-3.5-flash-lite"
T = [{"type": "url_context"}]


def consultar(titulo, prompt, mostrar_estructura=False, tools=T, modelo=MODELO):
    t0 = time.time()
    try:
        r = client.interactions.create(model=modelo, input=prompt, tools=tools)
    except Exception as e:
        print(f"[{titulo}] FALLO {type(e).__name__} {getattr(e, 'status_code', None)} {str(e)[:240]}")
        return None
    res = [s for s in r.steps if s.type == "url_context_result"]
    estados = []
    for s in res:
        d = s.model_dump()
        for item in d.get("result") or []:
            estados.append((str(item.get("status"))[:22], str(item.get("url") or item.get("retrieved_url"))[:55]))
    u = r.usage
    uso = {k: getattr(u, k, None) for k in ("input_tokens", "output_tokens", "tool_use_input_tokens", "total_tokens")} if u else {}
    anot = [a for s in r.steps if s.type == "model_output" for b in s.content if b.type == "text" for a in (b.annotations or [])]
    print(f"[{titulo}] {time.time() - t0:.0f} s | llamadas url={sum(s.type == 'url_context_call' for s in r.steps)} | estados={estados} | uso={uso} | citas={len(anot)}")
    if mostrar_estructura:
        for s in res[:1]:
            print("   estructura url_context_result:", {k: (type(v).__name__, str(v)[:90]) for k, v in s.model_dump().items() if v is not None and k != "signature"})
        for a in anot[:2]:
            print("   cita:", {k: (v if not isinstance(v, str) else v[:80]) for k, v in a.items()} if isinstance(a, dict) else a.model_dump())
    print(f"   -> {(r.output_text or '')[:230]!r}")
    return r


print("=== 1) comparar dos paginas y estructura ===")
consultar("comparar", "Compare these two pages in two sentences: https://example.com and https://httpbin.org/html", mostrar_estructura=True)

print("\n=== 2) tipos de contenido ===")
TIPOS = [
    ("JSON", "https://httpbin.org/json"), ("texto plano", "https://httpbin.org/robots.txt"), ("XML", "https://httpbin.org/xml"),
    ("PNG", "https://httpbin.org/image/png"), ("JPEG", "https://httpbin.org/image/jpeg"),
    ("PDF", "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"),
]
for nombre, url in TIPOS:
    consultar(nombre, f"In one short sentence, what is at {url} ?")

print("\n=== 3) NO soportados y casos de error ===")
NOPE = [
    ("YouTube", "https://www.youtube.com/watch?v=dQw4w9WgXcQ"), ("404", "https://httpbin.org/status/404"), ("401 (login)", "https://httpbin.org/basic-auth/u/p"),
    ("localhost", "http://localhost:8080/"), ("IP privada", "http://192.168.1.1/"), ("dominio inexistente", "https://no-existe-xyz-123456.invalid/"),
    ("redireccion", "https://httpbin.org/redirect-to?url=https://example.com"),
]
for nombre, url in NOPE:
    consultar(nombre, f"In one short sentence, what is at {url} ? If you cannot read it, say exactly why.")

print("\n=== 4) enlaces anidados (la doc: solo lee las URLs dadas) ===")
consultar("enlace anidado", "Read https://example.com. It has a link. Tell me the exact title of the page that link points to, only if you can read it; otherwise say you cannot.")

print("\n=== 5) limite de 20 URLs (21 URLs) ===")
urls = " ".join(f"https://httpbin.org/anything/{i}" for i in range(1, 22))
consultar("21 URLs", f"For each of these URLs, answer with the number at the end of the path, as a comma-separated list: {urls}")
urls20 = " ".join(f"https://httpbin.org/anything/{i}" for i in range(1, 21))
consultar("20 URLs", f"For each of these URLs, answer with the number at the end of the path, as a comma-separated list: {urls20}")

print("\n=== 6) url_context + google_search ===")
consultar("url + search (3.x)", "Find one recent news about the Python language and read the page. One sentence.", tools=[{"type": "url_context"}, {"type": "google_search"}])
