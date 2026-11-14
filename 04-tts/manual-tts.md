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

## `response_format` no es obligatorio
En `tts_sin_response_format.py` se quito `response_format={"type": "audio"}` y la peticion funciono igual (WAV de 24 kHz). Los demas scripts lo mantienen por claridad.

## Voces
- 30 voces predefinidas (Kore, Puck...). Otras formas: biblioteca extendida, diseno de voz, replica y remix.
- `client.voices.list(language_code=[...], gender=[...], pitch=[...], contexts=[...], type_=[...], search=..., page_size=...)` (`tts_voces.py`) **solo consulta**. Dentro de un filtro de lista es "O"; entre filtros distintos, "Y".
- **Voces latinoamericanas (`tts_voces_latam.py`, solo consulta):** el catalogo tiene **2 114 voces en 39 idiomas**. El espanol de Latinoamerica esta bajo **`es-419`** (419 = codigo de region de las Naciones Unidas para Latinoamerica): **86 voces**, con acento **Argentina (53)** y **Mexico (33)**; no hay dominicano ni colombiano. Mi filtro anterior (es-DO/MX/US) no encontraba nada porque ese codigo no existe. Tambien hay 22 voces `es-ES` ("Castilian Spanish"). Los nombres son de rol: `es-419-concierge-2`, `es-419-advisor-1`, `es-419-commercial-4`...
- **El `id` de una voz de la biblioteca SIRVE como `voice` en `speech_config`** (`tts_voces_propias.py`): `es-419-concierge-2` -> WAV de 5,6 s, 24 kHz, mono. (Se verifico el formato, **no se escucho**.)

### Disenar, remezclar y replicar voces (`tts_voces_propias.py`)

Se crean con `client.voices.create(voice={...}, store=True)`; `store=True` es **obligatorio** para voces `prompted`. La voz guardada devuelve un `id` (`voice_...`) que se usa como `voice` en `speech_config`; caduca **1 ano despues del ultimo uso** (medido: `expire_time` a 1 ano) y cada proyecto tiene un maximo de voces activas.

| Tipo | Como se crea | Resultado medido |
| :--- | :--- | :--- |
| **Diseno** | `{"type": "prompted", "language_code": "es-419", "prompted": {"input": "<descripcion de la voz>"}}` | **funciono**: "mujer calida y tranquila con acento dominicano del Caribe" -> voz `voice_...` y WAV de 6,5 s |
| **Remix** | igual, con `prompted.base_voice` (nombre de una voz predefinida, p. ej. `Kore`, o id de una voz propia); el `input` describe cambios **relativos** | **403 `PERMISSION_DENIED`: "Voice edit and remix requires Paid Quota Tier 1 or higher."** (solo plan de pago) |
| **Replica** | `{"type": "replicated", "replicated": {"consent_audio": ...}}` + `sample_audio` | **no probado**: exige grabaciones de referencia y de consentimiento de una persona |

- `voices.get(id=...)`, `voices.list(type_=["prompted"])` y `voices.delete(id=...)` funcionan. **`delete` quiere el id DESNUDO** (`voice_abc123`): con `voices/voice_abc123` da **404** y la voz se queda guardada (me paso la primera vez; la borre despues y `list` quedo en `[]`).
- Que la voz disenada **suene dominicana** no se pudo comprobar (no se escucha desde aqui): solo se sabe que se creo y que el audio se genero.
