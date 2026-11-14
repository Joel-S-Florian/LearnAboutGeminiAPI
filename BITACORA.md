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
- Mezclar herramienta integrada + funcion propia (2026-11-14): `code_execution` + funcion propia **funciono** con `gemini-3.1-flash-lite` (turno 1: `code_execution_call`, `code_execution_result`, `function_call`; turno 2: respuesta; suma de los 20 primeros primos = 639). Con `gemini-2.5-flash`, `google_search` + funcion dio `400 "Built-in tools ({google_search}) and Function Calling cannot be combined"`: **los modelos 2.5 no admiten la mezcla**, solo 3.x/4 segun la doc. Con 3.x, `google_search` dio 429 (cuota). Por tanto el ejemplo de la doc (search + funcion) **no se pudo verificar**.
- MCP remoto (2026-11-14): `{"type": "mcp_server", "name": ..., "url": ...}`; Google se conecta al servidor y llama a sus herramientas (pasos `mcp_server_tool_call` / `mcp_server_tool_result`), sin `function_call` que atender. Con el servidor demo de la doc y el prompt "Check the weather in San Francisco." el modelo **invento fechas** (2023/2024/2025) y el servidor devolvio `Forecast failed with status 400` (5 intentos, 5 errores); el modelo termino disculpandose. Con la fecha en el prompt ("...for today, 2026-11-14") funciono a la primera. **Leccion:** si la herramienta pide datos que el prompt no da (fechas), el modelo los inventa; mirar `mcp_server_tool_result` (`is_error`, `result`) para ver el error real. Por que el servidor rechazo esas fechas concretas, **no verificado**.
- `computer_use` (2026-11-14): sin captura de pantalla y sin Playwright, el modelo (`gemini-3.5-flash-lite`) respondio con pasos `thought` + `function_call` (`navigate`, url de Google, con `intent`). **El modelo solo propone la accion; no la ejecuta**: ejecutarla y devolver una captura nueva (`function_result`) es trabajo del codigo. El bucle completo con Playwright **no se probo**.
- `file_search`: crea recursos persistentes en el proyecto; el script borra el store en `finally` (`delete(..., config={"force": True})`).
- Para que el modelo use herramientas **y** responda con un esquema, ver `06-salida-estructurada/herramientas.py` (**no verificado de punta a punta**: se bloqueo por cuota/timeout).

## Streaming y respuestas
- En streaming, filtrar eventos por `event.delta.type` (`"text"`, `"audio"`). Hay deltas `thought_signature` sin `.text` que rompen el codigo si se accede a `.text` directo.
- `output_text`, `output_image` y `output_audio` existen como atajos en este SDK.
- Los modelos "thinking" devuelven un paso `thought` antes de `model_output`: no asumir que `steps[0]` es el texto.

- **Streaming de function_call (2026-11-14): la doc de Python esta desfasada.** Dice filtrar `event.delta.type == "arguments"` y leer `delta.partial_arguments`. En la ejecucion real el tipo es **`"arguments_delta"`** y el trozo esta en **`delta.arguments`** (un string JSON, p. ej. `'{"location":"Paris"}'`). Con el codigo de la doc **no da error**: los argumentos quedan **vacios (`{}`)** en silencio. Leccion: en streaming, contar los tipos de evento recibidos (`Counter`) antes de confiar en un filtro. Aqui los argumentos llegaron en un solo delta; con otros prompts podrian llegar partidos **(no verificado)**.

- Function calling + `response_format` (2026-11-14): funciona (el esquema se repite en la peticion que lleva el `function_result`). **Una de dos ejecuciones devolvio `output_text` vacio** (`''`) y `model_validate_json` fallo con `Invalid JSON: EOF`; la repeticion dio el JSON correcto. Causa **no verificada**. Leccion: antes de validar con Pydantic, comprobar que `output_text` no este vacio y tener reintento.

- **"Malformed function call" reproducido (2026-11-14, `gemini-3.5-flash-lite`).** Con un `system_instruction` que exige un bloque `<UPDATE>` en texto antes de llamar a la herramienta, en 3 ejecuciones salio: 1 OK, 1 con la llamada **escrita como texto** dentro de `model_output` (`<default_api:get_current_temperature{location:Paris}/>`, sin paso `function_call`) y 1 con `status: failed` y `steps` **vacio/None**. Un codigo que haga `for s in r.steps` revienta con `TypeError: 'NoneType' object is not iterable` (me paso). Con la solucion preferida de la doc (`update()` como funcion), 3 de 3 ejecuciones dieron `update` + la funcion real. **Muestra minima (3 + 3 + otras 3 previas): no es una estadistica.** Leccion: comprobar `r.status` y `r.steps or []` antes de iterar, y no asumir que un `model_output` sin `function_call` es una respuesta final.

- **Esquemas complejos con `tool_choice: any` (2026-11-14, `gemini-3.5-flash-lite`):** niveles simple (1 herramienta), medio (5 herramientas, enums de 20), grande (20 herramientas, 8 propiedades, enums de 50, 2 niveles) -> **aceptados**. Nivel enorme (60 herramientas, 10 propiedades, enums de 100, 4 niveles) -> primero `503` (alta demanda) y al reintentar **`429`: "limit: 250000 input tokens per minute on Free Tier"**. **El `400 INVALID_ARGUMENT` de la doc no se reprodujo**: el limite que se toco fue el de tokens de entrada por minuto, porque las declaraciones tambien cuentan como entrada. Los umbrales del 400 siguen sin conocerse. Leccion: un esquema enorme puede costar cuota aunque la API lo acepte.

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
