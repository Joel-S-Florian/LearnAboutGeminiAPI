# LearnAboutGeminiAPI

Repositorio de aprendizaje personal sobre la **API de Gemini** de Google. El objetivo es entender cómo funciona paso a paso, sin delegar todo en la IA y sin dejar ningún tema en el tintero.

Cada commit representa un **episodio** de aprendizaje: un concepto entendido, un experimento realizado o una corrección aplicada.

## Contenido

- Scripts de ejemplo en Python que llaman a la API de Gemini.
- Notas y manuales en Markdown con los conceptos aprendidos.
- Un historial de commits que funciona como bitácora del progreso.

## Requisitos

- Python 3.10 o superior
- Una API Key de Gemini obtenida en [Google AI Studio](https://aistudio.google.com/)

## Uso general

1. Clona el repositorio:

   ```bash
   git clone https://github.com/Joel-S-Florian/LearnAboutGeminiAPI.git
   cd LearnAboutGeminiAPI
   ```

2. Instala el SDK oficial:

   ```bash
   pip install -U google-genai
   ```

3. Define tu API Key como variable de entorno **en la misma terminal** donde ejecutarás los scripts:

   ```cmd
   set GEMINI_API_KEY=tu_clave_real_aqui
   ```

4. Ejecuta cualquier script del repositorio:

   ```bash
   python pregunta_gemini.py
   ```

## Seguridad

**Nunca subas tu API Key al repositorio.** La clave debe vivir solo en la variable de entorno de tu terminal. Si usas un archivo `.env`, asegúrate de que esté en `.gitignore`.

## Convención de commits

- `feat:` nuevo concepto o funcionalidad aprendida y aplicada.
- `docs:` apuntes, manuales o documentación.
- `fix:` corrección de un error.

## Recursos

- [Documentación oficial del SDK de Google Gen AI para Python](https://googleapis.github.io/python-genai/)
- [Google AI Studio](https://aistudio.google.com/)
- [Repositorio del SDK en GitHub](https://github.com/googleapis/python-genai)

