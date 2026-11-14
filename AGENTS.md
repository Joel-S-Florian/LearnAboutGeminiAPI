# AGENTS.md — LearnAboutGeminiAPI

Repositorio de aprendizaje personal de Joel (estudiante de ingenieria de software) sobre la API de Gemini. El objetivo es **entender**, no acumular codigo: cada tema se explica paso a paso.

## Como trabajar con Joel
- Responde en **espanol**. Explica que hace cada parte del codigo, antes o despues de cambiarla.
- Usa diagramas **Mermaid** cuando ayuden (flujos, secuencias).
- **No afirmes causas que no verificaste.** Marca lo no probado como "no verificado" (en chat, en comentarios y en los manuales).
- **No hagas commit ni push** hasta que Joel lo pida; son dos pasos separados.
- Un tema a la vez: tema y subtemas, sin saltar.
- Al cerrar cada sesion, actualiza la seccion "Donde vamos" de este archivo.
- Anota en `BITACORA.md` cada leccion verificada ("si X falla, pasa Y") apenas ocurra, con fecha; lo supuesto va como "no verificado".

## Estructura
```
NN-nombre-del-tema/   una carpeta por tema, en orden de estudio
  script.py ...       codigo comentado en espanol
  manual-*.md         apunte del tema (con Mermaid)
assets/               archivos de ENTRADA (sample.jpg ...), versionados
salidas/              archivos generados o descargados (ignorada por git)
_borradores/          pruebas sueltas (ignorada por git)
AGENTS.md  CLAUDE.md  README.md
```
Temas actuales: ver la tabla del `README.md`. Un tema nuevo = carpeta nueva con el siguiente numero.

## Reglas del codigo
- Comentarios en espanol **sin tildes ni enie** (evita problemas de codificacion en Windows), en el estilo de `01-primera-llamada/pregunta_gemini.py`.
- Rutas con `Path(__file__)` (ver `04-tts/tts.py`): los scripts deben funcionar ejecutados desde la raiz o desde su carpeta. Entradas desde `assets/`, salidas a `salidas/`.
- API key solo en la variable de entorno `GEMINI_API_KEY`. Nunca en el codigo ni en commits; `.env` esta ignorado.
- Ejecutar desde la raiz: `python 04-tts/tts.py`.

## Git
- Un commit por **episodio** de aprendizaje: `feat:` concepto aplicado, `docs:` apuntes, `fix:` correccion.
- Si un script no se pudo verificar, dilo en el mensaje del commit.

## Entorno
- Windows, PowerShell, Python 3.13, `google-genai` 3.2.0 (Interactions API: `client.interactions.create(model=..., input=...)`).
- El SDK 3.2.0 lanza excepciones propias con el codigo HTTP en `e.status_code` (no `errors.ClientError`).
- `interaction.output_text`, `output_image` y `output_audio` existen en este SDK.

## Estado verificado (2026-11-14)
- Verificado ejecutando: imagen en Base64 + audio con `files.upload()`; backoff ante 503; TTS (un hablante, dos, etiquetas, streaming, formatos, voces); salida estructurada (cinco ejemplos); herramientas `google_search` (con `v1beta` y modelo 2.5), `code_execution`, `url_context`; function calling completo (seccion 9, 17 subtemas); MCP remoto; streaming de llamadas.
- **No verificado / fallo:** `03-generacion-imagen` (se colgo; limite 0/0 en el nivel gratuito); Lyria (limite 0/0); `google_maps` (429, limite 0/0); `google_search` + funcion propia (cuota); el `400` de esquemas complejos (no se reprodujo); audios de `salidas/` (formato y duracion comprobados, **no escuchados**); audio por URL directa (400, causa no confirmada).
- **Lecciones y trampas** (con fecha y evidencia): ver `BITACORA.md`.

## Donde vamos (actualizar al cerrar cada sesion)
Ultima actualizacion: 2026-11-14.

- **Guia en orden** (https://aistudio.google.com/docs/get-started; el contenido de cada seccion lo pega Joel o esta en `Others/`, carpeta sin versionar): hechas la 6 (imagen, TTS, Lyria: ver pendientes), 7 (salida estructurada), 8 (herramientas), 9 (funciones propias) y **10 (agentes gestionados, 24 subtemas; apunte: `09-agentes-gestionados/manual-agentes.md`)**. y **11 (segundo plano con modelos normales; carpeta `10-segundo-plano/`, apunte `manual-segundo-plano.md`)**. La 11 es la ultima de `get-started` segun Joel; **Siguiente: lo que Joel busque despues** (o los pendientes de abajo). Nota: la numeracion de las carpetas (01 a 10) NO coincide con la de las secciones de la guia (6 a 11).
- **Hecho:** 01 primera llamada · 02 imagen + audio (con reintentos) · 04 TTS (`manual-tts.md`) · 06 salida estructurada (`manual-salida-estructurada.md`) · 07 herramientas: `google_search`, `code_execution`, `url_context`, `file_search`, `google_maps`, `computer_use` · 08 funciones propias: 17 subtemas (bucle, casos de uso, cuatro pasos, stateless, paralelo, composicional, modos, multi-tool, multimodal, URI, MCP, streaming, esquema, buenas practicas, texto antes de herramienta, esquemas complejos).
- **Patrones del repo:** lista de modelos con respaldo (el primero que responde), `timeout` en milisegundos en `http_options`, y `v1beta` para `google_search`, TTS y Lyria.
- **Cuota (nivel gratuito, ver `rate_limit/*.json`, local, no versionado):** modelos flash normales 20 peticiones/dia, los "lite" 500/dia; Lyria, imagen y Maps con limite 0/0. Cuota por **proyecto**, no por clave.
- **Pendiente de Lyria/imagen:** `05-musica-lyria/lyria_clip.py` y `03-generacion-imagen`: sin resultado (se colgaron; limite 0/0). Necesitan facturacion para probarse.
- **TTS (hecho el 2026-11-14):** voces latinoamericanas = `es-419` (86 voces, acento Argentina/Mexico); el `id` de una voz de la biblioteca sirve en `speech_config`; diseno de voz funciona (borrar con el id DESNUDO); `response_format` NO es obligatorio. **Pendiente:** remix (403: exige plan de pago, Tier 1), replica (exige grabaciones y consentimiento de una persona) y **escuchar los WAV de `salidas/`** (solo se comprobo formato y duracion).
- **Herramientas (2026-11-14):** `file_search`: con el embedding por defecto (001) recupera bien; con `gemini-embedding-2` es erratico en espanol y fiable en ingles (matiz de T2.5, ver BITACORA). Salida estructurada + herramientas: google_search+esquema da 400 en 2.5 y 429 en 3.x (cuota 0/0); url_context+esquema funciona en 3.5-flash-lite. `computer_use` bucle completo HECHO (Playwright instalado; NO repetir `tools=` en el turno del `function_result`; `element_coordinate` es `[y, x]`). **Pendiente:** `google_maps` (cuota).
- **Agentes (carpeta 09):** todo lo que crea recursos (agentes guardados, triggers) se borra al final del script (`try/finally`). Cada ejecucion cuesta ~5K tokens de base y la cuota gratuita de Antigravity es 100K tokens/minuto: espaciar y poner `max_total_tokens`. Pendientes sin verificar: fuentes `repository`/`gcs`, credenciales guardadas, hooks, actualizar un agente, PDF/audio/video como entrada.
- **Guia Agents (`Others/Agents`, 2026-11-14):** E1 Entornos HECHO (fuentes, variables, API de entornos y de archivos, red, software; scripts `fuentes_entorno`, `variables_entorno`, `api_entornos`, `api_archivos`, `red_entorno`, `software_entorno` en carpeta 09). E2 Credenciales HECHO (CRUD, allowlist, variable de entorno, OAuth2 solo errores; scripts `credenciales_crud`, `credencial_allowlist`, `credencial_variable`, `credencial_oauth2`): el secreto es write-only y el proxy lo inyecta solo en cabeceras hacia dominios confiables; **sin probar:** OAuth2 con exito, credencial en `mcp_server`, repo privado con token real (exigen un proveedor o token real tuyo). E3 Hooks HECHO (bloqueo, matchers, fallos, privacidad/tamper y HTTP indirecto; scripts `hook_*.py`; **trampas:** un script de hook roto = allow silencioso, `deny` solo con `exit 0`, y un hook de contenedor se puede apagar editando `.agents/hooks.json`). E4 Deep Research SALTADO por decision de Joel (1-3 USD por tarea; el sondeo se colgo sin resultado y pudo dejar una tarea huerfana sin comprobar; ver BITACORA). E5 autoalojados HECHO solo en la parte de API (crear por REST, get/list, usar sin runtime se cuelga); **sin probar:** el CLI `gemini-api` y conectar un runtime (riesgo: en modo local ejecuta shell en el PC). **Sigue:** E6 marcos (solo lectura). **Regla nueva:** scripts largos o con coste, con `python -u` y a un archivo, no por tuberia. **Regla nueva:** todo script que cree un entorno lo guarda al instante (`background=True`) y lo borra en `finally`; el SDK avisa que Environments es experimental. Faltan por pegar: Agents in AI Studio, Pricing for agents, Gemini API CLI, Antigravity SDK, Google ADK.
- **Guia Tools (`Others/Tools`, 2026-11-14):** T1 combinar integradas + funciones HECHO (`07-herramientas/combinar_herramientas.py`; trampa: sin `signature` -> 400; `google_search`+funcion sigue sin verificar en 3.x). T2 File Search a fondo HECHO (T2.1 stores/documentos y T2.2 subir/importar/chunking y T2.3 metadatos y T2.4 PDF/paginas y T2.5 multimodal hechos: `fs_stores_documentos.py`, `fs_subir_importar_chunking.py`, `fs_metadatos.py`, `fs_pdf_paginas.py` (`page_number` correcto, pero la cita puede senalar un chunk que no respondio), `fs_multimodal.py` (imagenes solo con embedding-2; `media_id` + `download_media`); en la cita, `source` = texto del chunk y `custom_metadata`; un campo inexistente en el filtro falla en silencio; faltan citas con paginas, multimodal con embedding-2, salida estructurada y limites). T3 Code execution HECHO (T3.1 pasos/errores/limites, T3.2 archivos/graficos y T3.3 imagenes y T3.4 multi-turno/librerias hechos: `ce_pasos_errores.py`, `ce_archivos_graficos.py`, `ce_imagenes.py` (contar con codigo 6/6 vs 0/6), `ce_multiturno_librerias.py` (**un .txt/.json/.pdf generado por el codigo rompe el turno siguiente con previous_interaction_id; solo .csv y .png valen; quitar el bloque `document` del historial lo arregla**) (CSV como `document` sale ~3x mas barato que pegado; cuenta las imagenes recibidas, el texto puede mentir); el limite de tiempo NO es 30 s, sin internet, subprocess funciona; falta solo la combinacion con google_search en Gemini 3, sin verificar por la cuota). T4 URL context HECHO (`url_a_fondo.py`: comprueba `status` antes de fiarte; limite 20 URLs es todo-o-nada; `usage` con nombres distintos a la doc). T5 Google Search HECHO (`search_a_fondo.py`: **los indices de las citas son BYTES UTF-8**; las URLs citadas son redirecciones de vertexaisearch; `gemini-2.0-flash` ya no existe). T6 Computer use (seguridad) HECHO (`cu_seguridad.py`: `safety_decision` y `safety_acknowledgement` funcionan; la regla de confirmacion en `system_instruction` NO impidio pulsar Send; `excluded_predefined_functions` se esquiva con acciones equivalentes; deteccion de inyeccion sin demostrar). T7 Maps HECHO como sondeo (`maps_sondeo.py`: 429 en todos los modelos; unico resultado util: la validacion de campos desconocidos y las trampas de cuelgue). **Guia Tools (T1-T7) COMPLETA;** lo que queda sin verificar de ella necesita facturacion (google_search/Maps en Gemini 3). **Siguen** (no son de Tools): E6 marcos de agentes y secciones de AI Studio: Live API, Optimization, Guide, Resources, Policies.
- **Idea pendiente:** dos claves en el `.env` con cambio automatico solo ante 429.
- **Leccion de streaming:** filtrar por `delta.type`; en llamadas a funciones el tipo real es `arguments_delta` (la doc de Python dice `arguments`). Detalle en `BITACORA.md`.
