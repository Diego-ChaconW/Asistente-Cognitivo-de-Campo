"""
Aplicación principal de Streamlit para el chat RAG con manuales biomédicos.
"""
import streamlit as st
from app.config import load_config
from app.services.rag_pipeline import RAGPipeline

# Configurar página
st.set_page_config(
    page_title="Chat con Manuales Biomédicos",
    page_icon="🏥",
    layout="wide"
)

# Inicializar configuración
try:
    config = load_config()
except ValueError as e:
    st.error(f"Error de configuración: {str(e)}")
    st.stop()

# Inicializar pipeline RAG (una sola vez, usando cache)
@st.cache_resource
def get_rag_pipeline():
    """Inicializa y cachea el pipeline RAG."""
    return RAGPipeline(
        search_config=config.azure_search,
        openai_config=config.azure_openai
    )

rag_pipeline = get_rag_pipeline()

# Inicializar historial de chat en session_state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Título y descripción
st.title("🏥 Chat con Manuales Biomédicos")
st.markdown("""
**Aplicación RAG (Retrieval Augmented Generation)** para consultar manuales técnicos y de usuario 
de dispositivos biomédicos usando Azure AI Search y Azure OpenAI.

Esta herramienta está diseñada para ayudar a **field engineers** a encontrar información técnica 
durante el mantenimiento de equipos.
""")

# Sidebar con parámetros y configuración
with st.sidebar:
    st.header("⚙️ Configuración")
    
    # Parámetros ajustables
    top_k = st.slider(
        "Número de documentos a recuperar (top_k)",
        min_value=1,
        max_value=10,
        value=3,
        help="Cantidad de fragmentos de manuales que se usarán como contexto. Valores más bajos usan menos tokens y reducen el riesgo de límites de tasa."
    )
    
    temperature = st.slider(
        "Temperatura del modelo",
        min_value=0.0,
        max_value=1.0,
        value=1.0,
        step=0.1,
        help="Valores más bajos dan respuestas más deterministas. Nota: Algunos modelos solo soportan el valor por defecto (1.0)"
    )
    
    st.divider()
    
    st.info("💡 **Optimización de tokens**: El sistema limita automáticamente el tamaño del contexto para evitar límites de tasa. Los chunks muy largos se truncarán si es necesario.")
    
    st.divider()
    
    st.subheader("📖 Instrucciones de uso")
    st.markdown("""
    **Ejemplos de preguntas:**
    - "¿Cómo calibro el sensor de oxígeno del modelo X?"
    - "¿Cuál es el procedimiento de mantenimiento preventivo?"
    - "¿Qué código de error significa E-123?"
    - "¿Cómo cambio el filtro del dispositivo Y?"
    
    **Consejos:**
    - Sé específico con modelos y números de parte
    - Usa términos técnicos cuando los conozcas
    - Si no encuentras respuesta, reformula la pregunta
    """)
    
    # Botón para limpiar conversación
    if st.button("🗑️ Limpiar conversación", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# Cuerpo principal: historial de chat
st.subheader("💬 Conversación")

# Mostrar historial de mensajes
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Mostrar fuentes si existen (solo para mensajes del asistente)
        if message["role"] == "assistant" and "sources" in message:
            sources = message["sources"]
            if sources:
                st.markdown("---")
                st.markdown("**📚 Fuentes utilizadas:**")
                for i, source in enumerate(sources, 1):
                    source_name = source.get("source", "Unknown")
                    score = source.get("score", 0.0)
                    
                    source_text = f"{i}. {source_name}"
                    if score > 0:
                        source_text += f" - Relevancia: {score:.2f}"
                    
                    st.caption(source_text)

# Campo de entrada para nueva pregunta
if prompt := st.chat_input("Escribe tu pregunta sobre los manuales biomédicos..."):
    # Añadir mensaje del usuario al historial
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Mostrar mensaje del usuario
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generar respuesta usando RAG
    with st.chat_message("assistant"):
        with st.spinner("Buscando en los manuales y generando respuesta..."):
            try:
                # Llamar al pipeline RAG
                result = rag_pipeline.rag_answer(
                    user_question=prompt,
                    top_k=top_k,
                    temperature=temperature
                )
                
                answer = result["answer"]
                sources = result["sources"]
                
                # Mostrar respuesta
                st.markdown(answer)
                
                # Mostrar fuentes
                if sources:
                    st.markdown("---")
                    st.markdown("**📚 Fuentes utilizadas:**")
                    for i, source in enumerate(sources, 1):
                        source_name = source.get("source", "Unknown")
                        page = source.get("pageNumber")
                        score = source.get("score", 0.0)
                        
                        source_text = f"{i}. {source_name}"
                        if page is not None:
                            source_text += f" (pág. {page})"
                        if score > 0:
                            source_text += f" - Relevancia: {score:.2f}"
                        
                        st.caption(source_text)
                
                # Guardar respuesta en el historial
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": sources
                })
                
            except Exception as e:
                error_msg = f"❌ Error al procesar la pregunta: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg
                })

# Footer
st.divider()
st.caption("💡 Esta aplicación usa Azure AI Search para búsqueda semántica y Azure OpenAI para generación de respuestas.")

