# Generador de CV en HTML con OpenAI

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

---

## 🧩 Estructura del proyecto

```
├── app.py                # Interfaz principal con Streamlit
├── openai_client.py      # Módulo de conexión y llamada a la API de OpenAI
├── environment.yml       # Archivo para crear el entorno Conda
├── .env.example          # Ejemplo de archivo de configuración de la API Key
└── README.md             # Este archivo
```

### Descripción de archivos

- **app.py:**  
  Define la interfaz, la lógica principal y la integración con OpenAI. Gestiona cargas de archivos, configuración del modelo y renderizado del HTML generado.

- **openai_client.py:**  
  Contiene las funciones auxiliares de conexión con la API de OpenAI. Procesa imágenes y PDFs, y maneja la llamada a la API con los mensajes estructurados en el formato esperado por la **Responses API**.

- **environment.yml:**  
  Permite crear un entorno Conda con todas las dependencias necesarias para ejecutar la aplicación.

---

## ⚙️ Requisitos

### Dependencias principales

- Python 3.10 o superior  
- Streamlit  
- OpenAI SDK  
- Pillow  
- python-dotenv  

### Instalación

Puedes crear el entorno de forma automática usando Conda:

```bash
conda env create -f environment.yml
conda activate cv_maker
```

Asegúrate de crear un archivo `.env` en la raíz del proyecto con tu clave de OpenAI:

```
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
```

---

## 🖥️ Uso

1. Ejecuta la aplicación:
   ```bash
   streamlit run app.py
   ```
2. En la interfaz:
   - Escribe el *brief* con tu perfil, experiencia y objetivo profesional.  
   - (Opcional) Sube tu foto y código QR.  
   - Selecciona el modelo de OpenAI y el color de acento.  
   - Haz clic en **“Generar CV”**.  
3. Visualiza el resultado y descárgalo como `cv.html`.

---

## 📦 Ejemplo de uso

**Brief de entrada:**
> Ingeniero industrial con 10 años de experiencia en manufactura y mejora continua. Experto en Lean Six Sigma, análisis de datos con Power BI y automatización de procesos de calidad.

**Salida esperada:**  
Un documento HTML profesional con diseño limpio, secciones completas, redacción ATS-friendly y métricas de impacto, listo para impresión o envío digital.

---

## 🧠 Arquitectura y flujo

1. El usuario ingresa los datos mediante Streamlit.  
2. `app.py` genera el *prompt* del sistema (`SYSTEM_PROMPT`) con reglas estrictas sobre estructura y estilo.  
3. `openai_client.py` convierte los archivos subidos en objetos adecuados (`input_image` o `input_file`) y los envía junto al texto al modelo seleccionado.  
4. El modelo devuelve un HTML completo que se renderiza directamente en la app y puede descargarse.  

---

## 🔒 Seguridad

- Las claves API se leen desde el entorno y **nunca se almacenan en la app**.  
- Los archivos subidos se guardan temporalmente y se eliminan tras su uso.  
- No se guarda ni transmite información personal fuera del proceso de generación.

---

## 🧰 Personalización

Puedes adaptar este proyecto para:

- Usar otros templates HTML o temas visuales.  
- Cambiar el idioma o tono ajustando el `SYSTEM_PROMPT`.  
- Integrarlo con bases de datos, portales de empleo o generadores de portafolio.  

---

## 🧾 Licencia

Este proyecto está licenciado bajo **Creative Commons Attribution 4.0 International (CC BY 4.0)**.  
Puedes usarlo, modificarlo y compartirlo libremente, siempre que otorgues el crédito correspondiente al autor original.

Para más información, consulta los términos completos en:  
[https://creativecommons.org/licenses/by/4.0/](https://creativecommons.org/licenses/by/4.0/)

---
