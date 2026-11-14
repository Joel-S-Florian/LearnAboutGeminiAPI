# 07.7 computer_use: BUCLE COMPLETO con Playwright (Chromium visible).
# Ciclo: captura -> modelo propone accion (function_call) -> TU codigo la ejecuta -> nueva captura
# (function_result con imagen) -> repetir hasta que el modelo responda con texto o se acabe el tope.
# Los nombres y argumentos exactos de las acciones NO estan documentados en este repo: por eso el script
# IMPRIME cada accion propuesta y avisa al modelo si no sabe ejecutarla (en vez de adivinar en silencio).
# Coordenadas del modelo: 0-999 (se escalan al tamano real). Cada captura se guarda en salidas/computer_use/.
# Tarea inofensiva y publica; sin iniciar sesion. Si aparece un CAPTCHA, parar (no se resuelve).

import base64
import sys
from pathlib import Path

from google import genai
from playwright.sync_api import sync_playwright

SALIDAS = Path(__file__).resolve().parent.parent / "salidas" / "computer_use"
SALIDAS.mkdir(parents=True, exist_ok=True)
W, H = 1280, 800
MAX_VUELTAS = 6  # tope: cada vuelta es una peticion con imagen
MODELOS = ["gemini-3.5-flash-lite"]  # gemini-3.8-flash dio timeout de 90 s en la prueba de formato
# La portada de Wikipedia (con noticias del dia) dio 400 "safety violations" al enviar su captura (2026-11-14);
# por eso se usa una pagina estable. Se puede pasar otra tarea como argumento.
TAREA = (sys.argv[1] if len(sys.argv) > 1 else
         "Go to https://docs.python.org/3/, click the 'Tutorial' link, then tell me the title of the page you land on.")

client = genai.Client(http_options={"timeout": 90_000})
TOOLS = [{"type": "computer_use", "environment": "browser"}]


def px(v, total):
    """Coordenada 0-999 del modelo -> pixeles reales."""
    return int(float(v) / 1000 * total)


def ejecutar(page, nombre, a):
    """Ejecuta la accion pedida. Devuelve texto de aviso si no se pudo (se lo cuenta al modelo)."""
    if nombre == "navigate":
        page.goto(a["url"], wait_until="domcontentloaded")
    elif nombre in ("click", "click_at", "click_element"):
        # Argumentos reales vistos (2026-11-14): {'element_coordinate': [y, x]} en 0-999, o {'element_id': '11'}
        # (un id de elemento que este cliente NO sabe resolver: se le avisa al modelo)
        if "element_coordinate" in a:
            y, x = a["element_coordinate"]  # ORDEN [y, x] (verificado contra la captura; no es [x, y])
        elif "element_rect" in a:  # [ymin, xmin, ymax, xmax]: se hace clic en el centro
            y0, x0, y1, x1 = a["element_rect"]
            x, y = (x0 + x1) / 2, (y0 + y1) / 2
        elif "point" in a:  # tercera forma vista: {'point': {'x': 356, 'y': 383}}
            x, y = a["point"]["x"], a["point"]["y"]
        elif "x" in a:
            x, y = a["x"], a["y"]
        else:
            return f"Cannot resolve click arguments {a}: send element_coordinate [x, y] instead."
        page.mouse.click(px(x, W), px(y, H))
    elif nombre in ("type", "type_text_at"):
        if "x" in a and "y" in a:
            page.mouse.click(px(a["x"], W), px(a["y"], H))
        page.keyboard.type(a.get("text", ""))
        if a.get("press_enter"):
            page.keyboard.press("Enter")
    elif nombre in ("key", "key_combination", "press"):
        page.keyboard.press(a.get("key") or a.get("keys"))
    elif nombre in ("scroll", "scroll_document"):
        page.mouse.wheel(0, 600 if a.get("direction", "down") == "down" else -600)
    elif nombre == "wait":
        page.wait_for_timeout(1500)
    else:
        return f"Action '{nombre}' is not implemented in this client."
    page.wait_for_timeout(1000)
    return None


def captura(page, n):
    img = page.screenshot(type="png")
    (SALIDAS / f"paso_{n:02d}.png").write_bytes(img)
    return base64.b64encode(img).decode()


with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_context(viewport={"width": W, "height": H}).new_page()
    page.goto("about:blank")

    interaction = None
    for modelo in MODELOS:
        try:
            interaction = client.interactions.create(
                model=modelo, tools=TOOLS,
                input=[{"type": "text", "text": TAREA},
                       {"type": "image", "mime_type": "image/png", "data": captura(page, 0)}],
            )
            print("Modelo usado:", modelo)
            break
        except Exception as e:
            print(f"[{modelo}] fallo: {type(e).__name__} {getattr(e, 'status_code', None)} {str(e)[:200]}")
    if interaction is None:
        browser.close()
        sys.exit("Ningun modelo respondio.")

    for vuelta in range(1, MAX_VUELTAS + 1):
        llamadas = [s for s in interaction.steps if s.type == "function_call"]
        if not llamadas:
            break
        resultados = []
        for c in llamadas:
            print(f"[{vuelta}] accion: {c.name} {c.arguments}")
            try:
                aviso = ejecutar(page, c.name, c.arguments or {})
            except Exception as e:
                aviso = f"Action failed: {type(e).__name__}: {str(e)[:150]}"
            if aviso:
                print("    ->", aviso)
            resultados.append({
                "type": "function_result", "name": c.name, "call_id": c.id,
                "result": [{"type": "text", "text": aviso or f"OK. Current URL: {page.url}"},
                           {"type": "image", "mime_type": "image/png", "data": captura(page, vuelta)}],
            })
        interaction = client.interactions.create(
            model=modelo, previous_interaction_id=interaction.id, input=resultados)  # SIN tools: repetirlas da 400 (ver BITACORA)

    print("\nPasos finales:", [s.type for s in interaction.steps])
    print("Respuesta del modelo:", interaction.output_text)
    print("URL final:", page.url)
    browser.close()
