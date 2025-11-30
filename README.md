# Generador de CV en HTML con OpenAI

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.51-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-412991?style=for-the-badge&logo=openai&logoColor=white)
![License](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey?style=for-the-badge)
![Tests](https://img.shields.io/badge/Tests-pytest-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white)

![Pandas](https://img.shields.io/badge/Pandas-2.3-150458?style=flat-square&logo=pandas&logoColor=white)
![Pillow](https://img.shields.io/badge/Pillow-12.0-3776AB?style=flat-square&logo=python&logoColor=white)
![NumPy](https://img.shields.io/badge/NumPy-2.3-013243?style=flat-square&logo=numpy&logoColor=white)
![Conda](https://img.shields.io/badge/Conda-Environment-44A833?style=flat-square&logo=anaconda&logoColor=white)
![HTML5](https://img.shields.io/badge/HTML5-Output-E34F26?style=flat-square&logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-Styled-1572B6?style=flat-square&logo=css3&logoColor=white)

---

Aplicación desarrollada en **Python + Streamlit** que genera **currículums en HTML listos para imprimir**, a partir de un breve perfil profesional redactado por el usuario.  
El sistema aprovecha los modelos GPT de OpenAI para transformar un *brief* en un documento HTML completo basado en un **template estructurado, semántico y optimizado para ATS**.

---

## 🚀 Características principales

- **Interfaz web con Streamlit:** interfaz simple e intuitiva para ingresar datos y generar el CV.  
- **Generación automática de HTML:** el modelo produce un documento completo (`<!DOCTYPE html> ... </html>`) siguiendo estrictas reglas de formato y estilo.  
- **Template profesional incluido:** mantiene estructura fija con secciones de perfil, experiencia, educación, habilidades, idiomas, etc.  
- **Personalización de color:** permite definir un color de acento mediante un *color picker*.  
- **Soporte de imágenes:** opción de incluir fotografía y QR (LinkedIn o portafolio) embebidos en el HTML mediante Data URI.  
- **Procesamiento de archivos de contexto:** puedes subir documentos o imágenes de referencia que se envían como contexto adicional al modelo.  
- **Compatibilidad con múltiples modelos OpenAI:** configurable entre `gpt-4.1-mini`, `gpt-4.1`, `gpt-4o-mini`, y `gpt-4o`.
- **Configuración centralizada:** todas las constantes y parámetros en un solo archivo `config.py`.
- **Manejo robusto de errores:** reintentos automáticos con backoff exponencial para la API de OpenAI.
- **Suite de pruebas:** tests unitarios con pytest para garantizar la calidad del código.

---

## 🧩 Estructura del proyecto

```
├── app.py                    # Interfaz principal con Streamlit
├── openai_client.py          # Módulo de conexión y llamada a la API de OpenAI
├── config.py                 # Configuración centralizada del proyecto
├── environment.yml           # Archivo para crear el entorno Conda
├── requirements.txt          # Dependencias completas (pip freeze)
├── requirements.min.txt      # Dependencias mínimas
├── conda_requirements.txt    # Dependencias para Conda
├── convert_requirements.py   # Script para convertir requirements
├── pytest.ini                # Configuración de pytest
├── ui.bat                    # Script de inicio rápido (Windows)
├── CV.html                   # Ejemplo de CV generado
├── .env.example              # Ejemplo de archivo de configuración de la API Key
├── README.md                 # Este archivo
└── tests/                    # Suite de pruebas unitarias
    ├── __init__.py
    ├── test_app.py           # Tests de la aplicación principal
    ├── test_config.py        # Tests de configuración
    └── test_openai_client.py # Tests del cliente OpenAI
```

### Descripción de archivos principales

- **app.py:**  
  Define la interfaz, la lógica principal y la integración con OpenAI. Gestiona cargas de archivos, configuración del modelo y renderizado del HTML generado.

- **openai_client.py:**  
  Contiene las funciones auxiliares de conexión con la API de OpenAI. Procesa imágenes y PDFs, y maneja la llamada a la API con los mensajes estructurados en el formato esperado por la **Responses API**. Incluye reintentos automáticos con backoff exponencial para errores de rate limit y conexión.

- **config.py:**  
  Configuración centralizada del proyecto que incluye:
  - Modelos disponibles y configuración de tokens
  - Extensiones de archivo soportadas
  - Parámetros de UI (colores, dimensiones)
  - Configuración de logging
  - Mensajes de interfaz

- **environment.yml:**  
  Permite crear un entorno Conda con todas las dependencias necesarias para ejecutar la aplicación.

---

## ⚙️ Requisitos

### Dependencias principales

- Python 3.11 o superior  
- Streamlit 1.51+
- OpenAI SDK 1.109+
- Pillow 12.0+
- python-dotenv 1.2+
- Pandas 2.3+
- NumPy 2.3+

### Instalación

#### Opción 1: Conda (Recomendado)

```bash
conda env create -f environment.yml
conda activate cv_maker
```

#### Opción 2: pip

```bash
pip install -r requirements.min.txt
```

### Configuración

Crea un archivo `.env` en la raíz del proyecto con tu clave de OpenAI:

```env
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
```

---

## 🖥️ Uso

### Ejecución estándar

```bash
streamlit run app.py
```

### Ejecución rápida (Windows)

```cmd
ui.bat
```

### En la interfaz:

1. Escribe el *brief* con tu perfil, experiencia y objetivo profesional.  
2. (Opcional) Sube tu foto y código QR.  
3. Selecciona el modelo de OpenAI y el color de acento.  
4. Ajusta los tokens máximos según la complejidad del CV.
5. Haz clic en **"🚀 Generar CV"**.  
6. Visualiza el resultado y descárgalo como `cv.html`.

---

## 🧪 Pruebas

El proyecto incluye una suite de pruebas unitarias con pytest:

```bash
# Ejecutar todas las pruebas
pytest

# Ejecutar con cobertura
pytest --cov=. --cov-report=html

# Ejecutar pruebas específicas
pytest tests/test_app.py -v
pytest tests/test_openai_client.py -v
pytest tests/test_config.py -v
```

---

## 📦 Ejemplo de uso

**Brief de entrada:**
> Ingeniero industrial con 10 años de experiencia en manufactura y mejora continua. Experto en Lean Six Sigma, análisis de datos con Power BI y automatización de procesos de calidad.

**Salida esperada:**  
Un documento HTML profesional con diseño limpio, secciones completas, redacción ATS-friendly y métricas de impacto, listo para impresión o envío digital.

Puedes ver un ejemplo real generado con esta aplicación en el siguiente enlace:  
👉 [Ejemplo de CV generado](https://qualityanalytics.net/wp-content/uploads/2025/11/cv.html)

---

## 🧠 Arquitectura y flujo

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Usuario       │────▶│    app.py       │────▶│ openai_client.py│
│   (Streamlit)   │     │   (Interfaz)    │     │     (API)       │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │                        │
                               ▼                        ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │   config.py     │     │  OpenAI API     │
                        │ (Configuración) │     │  (GPT-4/4o)     │
                        └─────────────────┘     └─────────────────┘
```

1. El usuario ingresa los datos mediante Streamlit.  
2. `app.py` genera el *prompt* del sistema (`SYSTEM_PROMPT`) con reglas estrictas sobre estructura y estilo.  
3. `config.py` proporciona los parámetros de configuración centralizados.
4. `openai_client.py` convierte los archivos subidos en objetos adecuados (`input_image` o `input_file`) y los envía junto al texto al modelo seleccionado.  
5. El modelo devuelve un HTML completo que se renderiza directamente en la app y puede descargarse.  

---

## ⚙️ Configuración avanzada

### Modelos disponibles

| Modelo | Descripción | Uso recomendado |
|--------|-------------|-----------------|
| `gpt-4.1-mini` | Rápido y económico | CVs simples, iteraciones rápidas |
| `gpt-4.1` | Balance velocidad/calidad | Uso general |
| `gpt-4o-mini` | Multimodal, económico | CVs con imágenes de referencia |
| `gpt-4o` | Máxima calidad | CVs complejos, mejor redacción |

### Parámetros configurables (config.py)

```python
DEFAULT_MAX_TOKENS = 6000    # Tokens de respuesta
MIN_TOKENS = 1024            # Mínimo configurable
MAX_TOKENS = 8000            # Máximo configurable
DEFAULT_TEMPERATURE = 0.2    # Creatividad del modelo
API_TIMEOUT = 120.0          # Timeout en segundos
MAX_FILE_BYTES = 8_000_000   # Tamaño máximo de archivos (8 MB)
```

---

## 🔒 Seguridad

- Las claves API se leen desde el entorno y **nunca se almacenan en la app**.  
- Los archivos subidos se guardan temporalmente y se eliminan tras su uso.  
- No se guarda ni transmite información personal fuera del proceso de generación.
- Logging configurable que oculta datos sensibles (API keys ofuscadas).

---

## 🧰 Personalización

Puedes adaptar este proyecto para:

- Usar otros templates HTML o temas visuales modificando el `SYSTEM_PROMPT` en `app.py`.
- Cambiar el idioma o tono ajustando las instrucciones del sistema.
- Modificar los colores y parámetros de UI en `config.py`.
- Añadir nuevos modelos de OpenAI actualizando `AVAILABLE_MODELS`.
- Integrarlo con bases de datos, portales de empleo o generadores de portafolio.

---

## 👤 Autor

**Francisco González**  
Quality Analytics  
Noviembre 2025

---

## 🧾 Licencia

Este proyecto está licenciado bajo **Creative Commons Attribution 4.0 International (CC BY 4.0)**.  
Puedes usarlo, modificarlo y compartirlo libremente, siempre que otorgues el crédito correspondiente al autor original.

Para más información, consulta los términos completos en:  
[https://creativecommons.org/licenses/by/4.0/](https://creativecommons.org/licenses/by/4.0/)
