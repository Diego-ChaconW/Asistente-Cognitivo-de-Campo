"""
Pipeline RAG (Retrieval Augmented Generation) que orquesta la búsqueda
y generación de respuestas.
"""
from typing import Dict, List, Optional
from app.services.azure_search_client import AzureSearchClient
from app.services.azure_openai_client import AzureOpenAIClient
from app.config import AzureSearchConfig, AzureOpenAIConfig


class RAGPipeline:
    """Pipeline que implementa el patrón RAG completo."""
    
    def __init__(
        self,
        search_config: AzureSearchConfig,
        openai_config: AzureOpenAIConfig
    ):
        """
        Inicializa el pipeline RAG con los clientes necesarios.
        
        Args:
            search_config: Configuración de Azure AI Search.
            openai_config: Configuración de Azure OpenAI.
        """
        self.search_client = AzureSearchClient(search_config)
        self.openai_client = AzureOpenAIClient(openai_config)
        
        # Prompt del sistema para el modelo
        self.system_prompt = """Eres un asistente especializado para field engineers de dispositivos biomédicos. 
Tu función es ayudar a los técnicos a encontrar información en los manuales técnicos y de usuario.

INSTRUCCIONES:
- Usa ÚNICAMENTE la información proporcionada en el contexto de los manuales.
- Si el contexto no contiene información suficiente para responder la pregunta, di claramente: "No encontré información suficiente en los manuales para responder esta pregunta."
- Proporciona respuestas claras, concisas y técnicas.
- Si mencionas procedimientos, sé específico sobre los pasos.
- Si hay información sobre modelos o números de parte, inclúyela en tu respuesta."""
    
    def rag_answer(
        self,
        user_question: str,
        top_k: int = 3,
        temperature: float = 1.0
    ) -> Dict:
        """
        Ejecuta el pipeline RAG completo: búsqueda + generación de respuesta.
        
        Args:
            user_question: Pregunta del usuario.
            top_k: Número de documentos a recuperar de Azure Search.
            temperature: Temperatura para la generación del modelo.
        
        Returns:
            Diccionario con:
                - "answer": texto de la respuesta generada.
                - "sources": lista de fuentes usadas (cada fuente es un dict con
                            "source", "pageNumber", "score", etc.).
        """
        try:
            # Paso 1: Buscar documentos relevantes en Azure AI Search
            search_results = self.search_client.search_documents_text_only(
                query=user_question,
                top_k=top_k
            )
            
            # Paso 2: Validar que se encontraron resultados
            if not search_results or len(search_results) == 0:
                return {
                    "answer": "No se encontró información relevante en los manuales para responder tu pregunta. Por favor, intenta reformularla o usar términos más específicos.",
                    "sources": []
                }
            
            # Paso 3: Extraer y limitar fragmentos de texto (campo "content")
            # Aplicar límites para evitar exceder el límite de tokens
            MAX_CHARS_PER_CHUNK = 2000  # Máximo de caracteres por chunk
            MAX_TOTAL_CONTEXT = 6000    # Máximo total de caracteres en el contexto
            
            context_chunks = []
            total_chars = 0
            
            for doc in search_results:
                content = doc.get("content", "")
                if not content:
                    continue
                
                # Truncar chunks muy largos
                if len(content) > MAX_CHARS_PER_CHUNK:
                    content = content[:MAX_CHARS_PER_CHUNK] + "... [texto truncado]"
                
                # Verificar si añadir este chunk excedería el límite total
                chunk_size = len(content)
                if total_chars + chunk_size > MAX_TOTAL_CONTEXT:
                    # Si ya tenemos al menos un chunk, parar aquí
                    if context_chunks:
                        break
                    # Si es el primer chunk y es muy grande, truncarlo más
                    content = content[:MAX_TOTAL_CONTEXT] + "... [texto truncado]"
                    context_chunks.append(content)
                    break
                
                context_chunks.append(content)
                total_chars += chunk_size
            
            if not context_chunks:
                return {
                    "answer": "Se encontraron documentos pero no contenían texto útil. Por favor, intenta otra pregunta.",
                    "sources": []
                }
            
            # Paso 4: Generar respuesta usando Azure OpenAI con el contexto
            answer = self.openai_client.generate_response(
                system_prompt=self.system_prompt,
                user_message=user_question,
                context_chunks=context_chunks,
                temperature=temperature
            )
            
            # Paso 5: Preparar información de fuentes
            # Los resultados ya vienen con el campo "source" mapeado desde metadata_storage_name
            sources = []
            for doc in search_results:
                source_info = {
                    "source": doc.get("source", "Unknown"),  # Nombre del PDF
                    "score": doc.get("score", 0.0)  # Score de relevancia
                }
                # Opcional: incluir path para depuración si es necesario
                if "path" in doc:
                    source_info["path"] = doc["path"]
                
                sources.append(source_info)
            
            return {
                "answer": answer,
                "sources": sources
            }
            
        except Exception as e:
            # Manejo de errores con mensajes más específicos
            error_message = str(e)
            
            # Si el error ya tiene un mensaje claro (como rate limit), usarlo directamente
            if "Límite de tasa alcanzado" in error_message or "rate limit" in error_message.lower():
                return {
                    "answer": f"⚠️ **Límite de tasa alcanzado**\n\n{error_message}\n\nPor favor, espera un momento antes de hacer otra pregunta.",
                    "sources": []
                }
            
            # Otros errores
            return {
                "answer": f"❌ **Error al procesar tu pregunta**\n\n{error_message}\n\nPor favor, intenta de nuevo o verifica tu configuración de Azure.",
                "sources": []
            }

