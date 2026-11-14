# AGENTS.md — LearnAboutGeminiAPI

Repositorio de aprendizaje personal de Joel (estudiante de ingenieria de software) sobre la API de Gemini. El objetivo es **entender**, no acumular codigo: cada tema se explica paso a paso.

## Como trabajar con Joel
- Responde en **espanol**. Explica que hace cada parte del codigo, antes o despues de cambiarla.
- Usa diagramas **Mermaid** cuando ayuden (flujos, secuencias).
- **No afirmes causas que no verificaste.** Marca lo no probado como "no verificado" (en chat, en comentarios y en los manuales).
- **No hagas commit ni push** hasta que Joel lo pida; son dos pasos separados.
- Un tema a la vez: tema y subtemas, sin saltar.
- Al cerrar cada sesion, actualiza la seccion "Donde vamos" de este archivo.

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

## Estado verificado (2026-11-12)
- Verificado: imagen en Base64 + audio subido con `client.files.upload()` en una misma peticion; reintento con backoff ante 503; TTS de uno y de dos hablantes (WAV 24 kHz mono, escuchado: no).
- Audio por URL directa dio 400 `invalid_request`; **causa no confirmada**.
- **No verificado:** `03-generacion-imagen/imagen_generada.py` (la llamada se colgo >10 min); si `response_format` es obligatorio en TTS; que `style` y el idioma suenen como se espera.

## Donde vamos (actualizar al cerrar cada sesion)
Ultima actualizacion: 2026-11-13.

- **Hecho:** 01 primera llamada · 02 imagen + audio en una peticion (con reintentos) · 04 TTS: un hablante, dos hablantes, etiquetas y `style`, streaming, formatos de salida, `voices.list()` (apunte: `04-tts/manual-tts.md`).
- **En curso: 05 Lyria 3.5 (generar musica).** `05-musica-lyria/lyria_clip.py`. Los modelos Lyria dieron 404 con la version de API por defecto; **hay que usar `http_options={"api_version": "v1beta"}`** (con v1beta, `models.list()` pasa de 28 a 64 modelos e incluye Lyria). Leccion general: si un modelo de la doc da 404, probar v1beta antes de culpar a la cuenta.
- **Siguiente: seccion 7 "Use structured output"** de https://aistudio.google.com/docs/get-started.
- **Pendiente de TTS:** diseno, remix y replica de voces (crean recursos guardados en el proyecto: hasta 200, con caducidad); buscar voces latinoamericanas con `search`/`accent`; comprobar que el `id` de una voz de la biblioteca sirve en `speech_config`.
- **Por verificar:** `03-generacion-imagen` (se colgo; reintentar con un `timeout` en la llamada); si `response_format` es obligatorio en TTS; escuchar los WAV de `salidas/`.
- **Orden acordado:** terminar TTS -> Lyria 3.5 (generar musica) -> seccion **7. Use structured output** de https://aistudio.google.com/docs/get-started (y seguir esa guia en orden).
- **Por estudiar despues:** musica con Lyria 3.5 (clip y cancion completa, letras, imagen a musica); generacion de imagenes: relaciones de aspecto, edicion, referencias.
