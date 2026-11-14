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
- **No verificado / fallo:** `03-generacion-imagen` (se colgo; limite 0/0 en el nivel gratuito); Lyria (limite 0/0); `google_maps` (429, limite 0/0); `file_search` (indexa pero el modelo no recupera, causa desconocida); `google_search` + funcion propia (cuota); el `400` de esquemas complejos (no se reprodujo); audios de `salidas/` (formato y duracion comprobados, **no escuchados**); `response_format` obligatorio en TTS; audio por URL directa (400, causa no confirmada).
- **Lecciones y trampas** (con fecha y evidencia): ver `BITACORA.md`.

## Donde vamos (actualizar al cerrar cada sesion)
Ultima actualizacion: 2026-11-14.

- **Guia en orden** (https://aistudio.google.com/docs/get-started; el contenido de cada seccion lo pega Joel o esta en `Others/`, carpeta sin versionar): hechas la 6 (imagen, TTS, Lyria: ver pendientes), 7 (salida estructurada), 8 (herramientas), 9 (funciones propias) y **10 (agentes gestionados, 24 subtemas; apunte: `09-agentes-gestionados/manual-agentes.md`)**. **Siguiente: seccion 11** (Joel la pega o la deja en `Others/`).
- **Hecho:** 01 primera llamada · 02 imagen + audio (con reintentos) · 04 TTS (`manual-tts.md`) · 06 salida estructurada (`manual-salida-estructurada.md`) · 07 herramientas: `google_search`, `code_execution`, `url_context`, `file_search`, `google_maps`, `computer_use` · 08 funciones propias: 17 subtemas (bucle, casos de uso, cuatro pasos, stateless, paralelo, composicional, modos, multi-tool, multimodal, URI, MCP, streaming, esquema, buenas practicas, texto antes de herramienta, esquemas complejos).
- **Patrones del repo:** lista de modelos con respaldo (el primero que responde), `timeout` en milisegundos en `http_options`, y `v1beta` para `google_search`, TTS y Lyria.
- **Cuota (nivel gratuito, ver `rate_limit/*.json`, local, no versionado):** modelos flash normales 20 peticiones/dia, los "lite" 500/dia; Lyria, imagen y Maps con limite 0/0. Cuota por **proyecto**, no por clave.
- **Pendiente de Lyria/imagen:** `05-musica-lyria/lyria_clip.py` y `03-generacion-imagen`: sin resultado (se colgaron; limite 0/0). Necesitan facturacion para probarse.
- **Pendiente de TTS:** diseno, remix y replica de voces (crean recursos guardados: hasta 200, con caducidad); voces latinoamericanas; comprobar que el `id` de una voz sirve en `speech_config`.
- **Pendiente de herramientas:** `file_search` (no recupera); `google_maps` (cuota); bucle completo de `computer_use` con Playwright; salida estructurada + herramientas (`06-salida-estructurada/herramientas.py`, sin verificar).
- **Agentes (carpeta 09):** todo lo que crea recursos (agentes guardados, triggers) se borra al final del script (`try/finally`). Cada ejecucion cuesta ~5K tokens de base y la cuota gratuita de Antigravity es 100K tokens/minuto: espaciar y poner `max_total_tokens`. Pendientes sin verificar: fuentes `repository`/`gcs`, credenciales guardadas, hooks, actualizar un agente, PDF/audio/video como entrada.
- **Idea pendiente:** dos claves en el `.env` con cambio automatico solo ante 429.
- **Leccion de streaming:** filtrar por `delta.type`; en llamadas a funciones el tipo real es `arguments_delta` (la doc de Python dice `arguments`). Detalle en `BITACORA.md`.
