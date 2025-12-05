# 🏥 Azure RAG Chat - Chat con Manuales Biomédicos

Aplicación de chat basada en el patrón **RAG (Retrieval Augmented Generation)** que permite a field engineers consultar información técnica de manuales de dispositivos biomédicos usando Azure AI Search y Azure OpenAI.

## 📋 Descripción del Proyecto

Esta aplicación está diseñada para que los **field engineers** puedan hacer preguntas sobre manuales técnicos y de usuario de dispositivos biomédicos durante el mantenimiento de equipos. La aplicación:

1. **Recibe preguntas** del usuario a través de una interfaz de chat en Streamlit.
2. **Busca información relevante** en un índice de Azure AI Search que contiene chunks de manuales biomédicos.
3. **Genera respuestas contextualizadas** usando Azure OpenAI con el contexto recuperado.

## 🏗️ Arquitectura

La aplicación utiliza una arquitectura RAG con los siguientes componentes:

- **Frontend**: Streamlit (interfaz de chat interactiva)
- **Motor de búsqueda**: Azure AI Search (índice con chunks de manuales biomédicos)
- **Modelo de lenguaje**: Azure OpenAI (generación de respuestas contextualizadas)
- **Patrón**: RAG (Retrieval Augmented Generation)

### Flujo de datos:

```
Usuario → Streamlit UI → RAG Pipeline → Azure AI Search (búsqueda)
                                              ↓
                                    Contexto recuperado
                                              ↓
                                    Azure OpenAI (generación)
                                              ↓
                                    Respuesta + Fuentes → Usuario
```

## 🔧 Requisitos Previos

Antes de ejecutar la aplicación, necesitas:

1. **Cuenta de Azure** con acceso a:
   - Azure AI Search (servicio creado)
   - Azure OpenAI (recurso con deployment de modelo de chat, por ejemplo GPT-4 o GPT-3.5-turbo)

2. **Índice de Azure AI Search**:
   - Nombre del índice: **biomed-manuals-demo-index**
   - El índice debe estar creado y poblado con chunks de manuales biomédicos (PDFs procesados)
   - Los manuales deben estar subidos a Azure Blob Storage y procesados mediante un indexer o el wizard de "Import Data" en Azure Portal
   - Campos del índice que usa la aplicación:
     - `content` (String, searchable): Texto de los manuales
     - `metadata_storage_name` (String, filterable, sortable, facetable): Nombre del archivo PDF (mostrado como "source" en la UI)
     - `metadata_storage_path` (String, key): Clave interna del documento

3. **Python 3.x** instalado (recomendado 3.8+)

4. **Variables de entorno** configuradas (ver sección de configuración)

## 📦 Instalación

### 1. Clonar el repositorio

```bash
git clone <url-del-repositorio>
cd azure-rag-chat
```

### 2. Crear y activar entorno virtual

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Crea un archivo `.env` en la raíz del proyecto basándote en `.env.example`:

```bash
cp .env.example .env
```

Edita el archivo `.env` y completa con tus credenciales de Azure:

```env
# Azure AI Search Configuration
AZURE_SEARCH_ENDPOINT="https://<tu-servicio-search>.search.windows.net"
AZURE_SEARCH_INDEX="biomed-manuals-demo-index"
AZURE_SEARCH_API_KEY="<tu-api-key-search>"

# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT="https://<tu-recurso-openai>.openai.azure.com"
AZURE_OPENAI_API_KEY="<tu-api-key-openai>"
AZURE_OPENAI_DEPLOYMENT="<nombre-del-deployment-del-modelo>"

# Streamlit Configuration (opcional)
STREAMLIT_SERVER_PORT="8501"
```

## 🚀 Ejecutar la Aplicación

Una vez configurado todo, ejecuta:

```bash
streamlit run app/main.py
```

La aplicación se abrirá automáticamente en tu navegador en `http://localhost:8501`.

## 📁 Estructura del Proyecto

```
azure-rag-chat/
├── app/
│   ├── __init__.py
│   ├── main.py                    # Aplicación principal de Streamlit
│   ├── config.py                  # Gestión de configuración y variables de entorno
│   └── services/
│       ├── __init__.py
│       ├── azure_search_client.py # Cliente para Azure AI Search
│       ├── azure_openai_client.py # Cliente para Azure OpenAI
│       └── rag_pipeline.py        # Pipeline RAG que orquesta todo
├── docs/
│   ├── search-index-demo.json          # Esquema simplificado de índice (demo)
│   └── search-index-prod-example.json  # Esquema completo para producción
├── .env.example                  # Plantilla de variables de entorno
├── requirements.txt              # Dependencias del proyecto
└── README.md                     # Este archivo
```

## 📊 Esquema del Índice

### Índice Real en Azure (`biomed-manuals-demo-index`)

La aplicación está configurada para trabajar con el índice **biomed-manuals-demo-index** que debe estar creado en Azure AI Search. Este índice utiliza el siguiente esquema:

**Campos principales que usa la aplicación:**
- `content` (String, searchable, retrievable): Texto extraído de los chunks de los manuales biomédicos. Este es el campo principal sobre el que se realiza la búsqueda textual.
- `metadata_storage_name` (String, filterable, sortable, facetable, retrievable): Nombre del archivo PDF de origen. La aplicación lo mapea internamente como "source" para mostrarlo en la interfaz.
- `metadata_storage_path` (String, key, retrievable): Ruta de almacenamiento del documento. Este campo es la clave (key) del índice.

**Notas:**
- El índice no incluye campos como `id`, `source` directo, `pageNumber`, `contentVector` ni configuración de búsqueda vectorial.
- La aplicación realiza búsqueda textual estándar sobre el campo `content`.
- Los archivos JSON en `docs/` (`search-index-demo.json` y `search-index-prod-example.json`) fueron diseños iniciales de ejemplo, pero la implementación actual está adaptada al esquema real del índice creado en Azure Portal.

## 🎯 Uso de la Aplicación

1. **Abre la aplicación** en tu navegador (se abre automáticamente al ejecutar Streamlit).

2. **Ajusta parámetros** en la barra lateral (opcional):
   - `top_k`: Número de documentos a recuperar (1-10)
   - `temperature`: Temperatura del modelo (0.0-1.0)

3. **Escribe tu pregunta** en el campo de chat. Ejemplos:
   - "¿Cómo calibro el sensor de oxígeno del modelo X?"
   - "¿Cuál es el procedimiento de mantenimiento preventivo?"
   - "¿Qué código de error significa E-123?"
   - "¿Cómo cambio el filtro del dispositivo Y?"

4. **Revisa la respuesta** y las fuentes utilizadas (nombre del PDF y página).

5. **Continúa la conversación** haciendo más preguntas.

6. **Limpia la conversación** usando el botón en la barra lateral cuando quieras empezar de nuevo.

## 🔍 Características

- ✅ Interfaz de chat intuitiva con Streamlit
- ✅ Búsqueda semántica en manuales biomédicos
- ✅ Generación de respuestas contextualizadas
- ✅ Visualización de fuentes (PDF y página)
- ✅ Parámetros ajustables (top_k, temperature)
- ✅ Manejo de errores básico
- ✅ Historial de conversación

## 🚧 Mejoras Futuras

Algunas mejoras que se podrían implementar:

- **Carga de datos desde código**: Script para subir y procesar PDFs automáticamente al índice
- **Soporte multiidioma**: Detección de idioma y respuestas en múltiples idiomas
- **Filtros avanzados**: Filtrar por modelo, fabricante, tipo de manual desde la UI
- **Autenticación de usuarios**: Sistema de login para control de acceso
- **Logging y trazabilidad**: Registro de preguntas, respuestas y métricas de uso
- **Búsqueda híbrida mejorada**: Integración completa de búsqueda vectorial + texto
- **Streaming de respuestas**: Mostrar la respuesta mientras se genera (mejor UX)
- **Exportación de conversaciones**: Guardar historiales de chat en PDF o texto

## 📝 Notas Técnicas

- La aplicación usa **búsqueda por texto** por defecto. El código está preparado para usar búsqueda vectorial si proporcionas embeddings.
- El modelo de Azure OpenAI debe ser un modelo de **chat** (por ejemplo, GPT-4, GPT-3.5-turbo).
- La versión de la API de Azure OpenAI usada es `2024-02-15-preview` (ajustable en `azure_openai_client.py`).
- Los chunks de los manuales deben estar previamente indexados en Azure AI Search.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un issue o pull request si tienes sugerencias o mejoras.

## 📄 Licencia

Este proyecto es una demo educativa. Ajusta la licencia según tus necesidades.

---

**Desarrollado con ❤️ para field engineers de dispositivos biomédicos**

