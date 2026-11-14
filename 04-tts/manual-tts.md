# 04. Text-to-speech (TTS)
Los modelos TTS reciben **solo texto** y devuelven **solo audio**. Se les da el texto exacto a leer; el estilo va aparte.

Scripts: `tts.py` (un hablante), `tts_dos_hablantes.py`, `tts_etiquetas.py`. SDK `google-genai` 3.2.0, modelo `gemini-3.8-flash-tts`.

## Dos formas de controlar como suena
| Alcance | Donde se pone | Ejemplos |
| :--- | :--- | :--- |
| Todo el turno | `speech_metadata.style` (texto libre) | `"whispered urgently"`, `"speaking slowly"` |
| Un momento puntual | etiqueta `<...>` dentro del `text` | `"Wait... <short pause> did you hear that? <sigh>"` |

## Etiquetas inline: son recomendadas, no un conjunto cerrado
La documentacion lista las siguientes como **recomendadas** ("include"), no como lista exhaustiva ni reservada. Pide usar corchetes angulares `<...>` y vocalizaciones **humanas** (no efectos de sonido como aplausos o golpes). Si el texto no esta en ingles, las etiquetas se dejan en ingles.
Lo que **no** esta documentado: que pasa con una etiqueta fuera de esta lista. No verificado.

| Tipo | Etiquetas |
| :--- | :--- |
| Respiracion | `<breath>` `<heavy breath>` `<exhales>` `<pant>` `<sigh>` / `<sighs>` `<yawn>` |
| Risa | `<laugh>` / `<laughter>` `<giggle>` `<chuckle>` / `<chuckles>` `<cackle>` `<snicker>` `<snort>` |
| Llanto | `<cry>` `<sob>` `<whimper>` |
| Gritos y quejidos | `<scream>` `<shout>` `<shriek>` `<cheer>` `<argh>` `<groan>` `<moan>` `<growl>` `<grunt>` `<grr>` `<hiss>` |
| Reacciones | `<gasp>` `<pff>` / `<phew>` `<tsk>` |
| Cuerpo | `<cough>` `<sneeze>` `<throat-clearing>` |
| Voz | `<whispers>` / `<whispering>` |
| Pausas | `<short pause>` `<long pause>` |

## Otras marcas de texto
- `...` y `--`: vacilacion o ritmo natural.
- MAYUSCULAS: enfasis en esa palabra (`This is a VERY important point!`).
- `|reaccion|` dentro de un turno (solo multi-hablante): reaccion del oyente sin cortar el turno, por ejemplo `"So the launch is Thursday |oh hmm| Are we ready?"`.

## Reglas de `style` (segun la documentacion)
- Texto libre: emocion, ritmo, volumen, prosodia.
- No lo uses para rasgos fijos del hablante (edad, genero, nombre, acento permanente): para eso, otra voz.
- Lo mas estable: una voz bien elegida y `style` vacio o corto, igual en todos los turnos.

## Idioma
No se configura: el modelo lo detecta del texto. `gemini-3.8-flash-tts` lista mas de 130 idiomas, entre ellos el espanol.

## Streaming (`tts_streaming.py`)
`stream=True` devuelve un iterador de eventos: el audio llega en trozos (en la prueba, 25 trozos para una frase corta). Los trozos son **PCM crudo** (`audio/l16`, 24 kHz, mono, 16 bits) sin cabecera WAV; para guardar un `.wav` hay que escribirla (modulo `wave`).

## Formatos de salida (`tts_formatos.py`)
Sin stream el audio llega como WAV. Con `response_format={"type": "audio", "mime_type": ..., "sample_rate": ...}` se piden formatos crudos, sin cabecera (comprobado: no empiezan por `RIFF`):

| `mime_type` | Frecuencia | Uso |
| :--- | :--- | :--- |
| `audio/l16` | 24 kHz | PCM de 16 bits |
| `audio/mulaw` | 8 kHz | telefonia (America del Norte y Japon) |
| `audio/alaw` | 8 kHz | telefonia (Europa e internacional) |

Un reproductor normal no abre los crudos; habria que convertirlos a WAV.

## Voces
- 30 voces predefinidas (Kore, Puck...). Otras formas: biblioteca extendida, diseno de voz, replica y remix.
- `client.voices.list(language_code=[...], gender=[...], pitch=[...], contexts=[...], type_=[...], search=..., page_size=...)` (`tts_voces.py`) **solo consulta**. Dentro de un filtro de lista es "O"; entre filtros distintos, "Y".
- Prueba: con `language_code` de es-DO, es-MX, es-US y es-ES llegaron 22 voces, todas es-ES. **No verificado** si hay voces latinoamericanas bajo otros codigos ni si el `id` de la voz sirve como `voice` en `speech_config`.
- Diseno, replica y remix **crean recursos guardados** en el proyecto (hasta 200, con caducidad). Pendiente de estudiar.
