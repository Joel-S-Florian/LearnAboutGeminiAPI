# Bitacora de lecciones (si X falla, pasa Y)

Registro de lo que **comprobamos ejecutando** contra la API real, sobre todo lo que la
documentacion no dice o dice distinto. Cada entrada: **sintoma -> que significaba -> que hacer**.

Reglas de esta bitacora:
- Solo va aqui lo que se vio en una ejecucion. Lo supuesto se marca **(no verificado)**.
- Se anota la fecha. Los limites y modelos cambian: lo de hoy puede no valer manana.
- Cada leccion nueva se agrega al final de su seccion cuando ocurre, no al cerrar la sesion.

## Errores HTTP y excepciones

| Sintoma | Que significaba aqui | Que hacer |
| :--- | :--- | :--- |
| `404 model not found` en un modelo de la doc (Lyria) | Ese modelo solo existe en `v1beta`. Con la version por defecto `models.list()` daba 28 modelos; con v1beta, 64 | Crear el cliente con `http_options={"api_version": "v1beta"}` antes de culpar a la cuenta (2026-11-13) |
| `400` con `google_search` y mensaje "Search as tool is not enabled for api version v1" | El mensaje lo dice literal: la herramienta pide v1beta | `api_version="v1beta"` (2026-11-14). **Leer el mensaje completo del error**: aqui traia la solucion |
| `429 You exceeded your current quota` | Cuota del proyecto. Mensaje generico: no dice si es por minuto, por dia o de una herramienta | Mirar `ai.dev/rate-limit`. Ver la seccion Cuotas |
| `503` | Modelo saturado o caido en ese momento (`gemini-3.8-flash`, 2026-11-14) | Reintentar con backoff y/o pasar al siguiente modelo de una lista |
| `APITimeoutError` | El cliente se canto a si mismo el tiempo; el servidor no respondio | Poner `timeout` y tener lista de modelos. No se sabe la causa en el servidor **(no verificado)** |
| `e.status_code` | El SDK 3.2.0 lanza excepciones propias, no `errors.ClientError` | `getattr(e, "status_code", None)` |

## Timeouts y llamadas colgadas
- Sin `timeout`, una llamada puede colgarse horas (Lyria: ~9 h 40 min; imagen: >10 min). Siempre ponerlo.
- `timeout` va en **milisegundos** dentro de `http_options` y **si** funciona con `interactions` (lanza `APITimeoutError`).
- El `timeout` **no es un tope total**: el SDK reintenta por debajo. Con `timeout=40_000`, `gemini-3.8-flash` tardo 176 s en devolver un 503. No fiarse de que "40 s" sea el maximo real.
- Con `APITimeoutError` en una herramienta (`url_context`, `code_execution`), probar primero **una llamada simple sin herramientas** con el mismo modelo: aqui el culpable era el modelo, no la herramienta (2026-11-14).

## Modelos
- Los modelos de la doc (`gemini-4-hydrogen`, `gemini-4-carbon`) no estaban en la lista de Joel; se uso `gemini-3.8-flash`. Verificar con `client.models.list()`.
- Un modelo puede estar caido mientras los demas responden. Probar varios **a la vez** (hilos) en un solo script y usar una **lista de modelos con respaldo**: ver `07-herramientas/code_execution.py`.
- Orden de la lista: primero los modelos con mas cuota gratuita (los "lite": 500/dia frente a 20/dia en los flash normales, segun `rate_limit/*.json`).
- Cuando falla un modelo, atrapar `Exception` y pasar al siguiente es suficiente para pruebas. Para produccion, distinguir 429 (cambiar de modelo/clave) de 400 (el codigo esta mal: no reintentar).

## Cuotas (nivel gratuito, instantanea 2026-11-14 9:22, ver `rate_limit/`)
- Los limites son **por proyecto**, no por clave: dos claves del mismo proyecto comparten cuota; dos proyectos tienen cuotas separadas.
- La suscripcion PRO de la **app** de Gemini no es la cuota de la **API**.
- Modelos flash normales: 5 por minuto y **20 por dia**. Modelos lite: 500 por dia.
- Limite **0/0** en: Lyria, modelos de imagen, Maps y `Gemini 3 and newer` para la busqueda (la busqueda de Gemini 2.5 tiene 1.5K/dia). Encaja con que Lyria/imagen nunca respondieran; por que se colgaban en vez de dar error, **no verificado**.
- TTS: `Gemini 3.8 Flash TTS` solo 10 por dia y 3 por minuto.
- Los tokens leidos por `url_context` cuentan como entrada: un solo modelo llego a 214K de 250K tokens por minuto.

## Herramientas (`tools=[...]`)
- Cada herramienta es un dict con su `"type"`: `google_search`, `url_context`, `code_execution`, `file_search`, `google_maps`, `computer_use`, `function`...
- `google_search`: exige `v1beta`. Las citas estan en `content_block.annotations` (tipo `url_citation`) y **llegan repetidas** y como enlaces de redireccion de Google: deduplicar antes de mostrarlas.
- `url_context`: lee solo las URLs dadas, publicas. Una pagina puede **bloquear la lectura automatica** (Allrecipes lo hizo) y el modelo lo avisa en el texto en vez de fallar. Revisar los pasos `url_context_result` para ver el estado de cada URL.
- `code_execution`: los pasos distinguen `model_output` (texto), `code_execution_call` (codigo) y `code_execution_result` (salida). Verificado: suma de los 50 primeros primos = 5117.
- `file_search` (2026-11-14): el store se crea, el archivo se indexa (`documents.list` lo muestra `STATE_ACTIVE`, 449 bytes) y el modelo hace 3 busquedas (`file_search_call`/`file_search_result`), **pero respondio "no encontre nada"** con `gemini-3.5-flash-lite` en 3 intentos. Los pasos `file_search_result` **no traen el contenido recuperado** (solo `call_id`), asi que no se ve que devolvio la busqueda. Causa **no verificada** (¿modelo lite?, ¿pregunta?, ¿falta algo para `interactions`?). Siguiente prueba: otro modelo y una pregunta que repita palabras exactas del archivo.
- `google_maps` (2026-11-14): `429 quota` con los 4 modelos probados (2.5-flash, 3.5-flash-lite, 3.1-flash-lite, 3.6-flash). Coincide con el limite 0/0 de Maps en `rate_limit/*.json` (nivel gratuito); necesita facturacion para probarse. El codigo de `07-herramientas/google_maps.py` **no esta verificado** contra una respuesta real.
- `file_search`: crea recursos persistentes en el proyecto; el script borra el store en `finally` (`delete(..., config={"force": True})`).
- Para que el modelo use herramientas **y** responda con un esquema, ver `06-salida-estructurada/herramientas.py` (**no verificado de punta a punta**: se bloqueo por cuota/timeout).

## Streaming y respuestas
- En streaming, filtrar eventos por `event.delta.type` (`"text"`, `"audio"`). Hay deltas `thought_signature` sin `.text` que rompen el codigo si se accede a `.text` directo.
- `output_text`, `output_image` y `output_audio` existen como atajos en este SDK.
- Los modelos "thinking" devuelven un paso `thought` antes de `model_output`: no asumir que `steps[0]` es el texto.

## Archivos y audio
- Audio por URL directa dio `400 invalid_request` (causa **no confirmada**). Subirlo con `client.files.upload()` y usar el `uri` si funciona.
- TTS y Lyria requieren `v1beta`.
- Los audios generados se verificaron en formato y duracion, **no se han escuchado**.

## Buenas practicas que salieron de los fallos
1. Poner `timeout` en todo cliente.
2. Leer el mensaje **completo** del error antes de teorizar.
3. Aislar: una llamada simple sin herramientas separa "falla el modelo" de "falla la herramienta".
4. Mirar `ai.dev/rate-limit` antes de asumir un bug.
5. Guardar este tipo de hallazgos aqui apenas pasen.
6. Idea pendiente: dos claves en el `.env` con cambio automatico solo ante 429 (`e.status_code == 429`).
