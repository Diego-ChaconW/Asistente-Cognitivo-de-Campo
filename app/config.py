"""
Módulo de configuración para cargar variables de entorno y validar settings.
"""
import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Cargar variables de entorno desde archivo .env
load_dotenv()


@dataclass
class AzureSearchConfig:
    """Configuración para Azure AI Search."""
    endpoint: str
    api_key: str
    index_name: str


@dataclass
class AzureOpenAIConfig:
    """Configuración para Azure OpenAI."""
    endpoint: str
    api_key: str
    deployment_name: str


@dataclass
class AppConfig:
    """Configuración completa de la aplicación."""
    azure_search: AzureSearchConfig
    azure_openai: AzureOpenAIConfig
    streamlit_port: Optional[int] = None


def get_env_var(var_name: str, required: bool = True) -> str:
    """
    Obtiene una variable de entorno y valida que exista si es requerida.
    
    Args:
        var_name: Nombre de la variable de entorno.
        required: Si es True, lanza error si la variable no existe.
    
    Returns:
        Valor de la variable de entorno.
    
    Raises:
        ValueError: Si la variable es requerida y no existe.
    """
    value = os.getenv(var_name)
    if required and not value:
        raise ValueError(
            f"Variable de entorno requerida '{var_name}' no encontrada. "
            f"Por favor, crea un archivo .env basado en .env.example"
        )
    return value


def load_config() -> AppConfig:
    """
    Carga y valida la configuración desde variables de entorno.
    
    Returns:
        AppConfig con toda la configuración validada.
    
    Raises:
        ValueError: Si faltan variables de entorno requeridas.
    """
    # Azure AI Search
    search_endpoint = get_env_var("AZURE_SEARCH_ENDPOINT")
    search_api_key = get_env_var("AZURE_SEARCH_API_KEY")
    search_index = get_env_var("AZURE_SEARCH_INDEX")
    
    # Azure OpenAI
    openai_endpoint = get_env_var("AZURE_OPENAI_ENDPOINT")
    openai_api_key = get_env_var("AZURE_OPENAI_API_KEY")
    openai_deployment = get_env_var("AZURE_OPENAI_DEPLOYMENT")
    
    # Streamlit (opcional)
    streamlit_port_str = get_env_var("STREAMLIT_SERVER_PORT", required=False)
    streamlit_port = int(streamlit_port_str) if streamlit_port_str else None
    
    return AppConfig(
        azure_search=AzureSearchConfig(
            endpoint=search_endpoint,
            api_key=search_api_key,
            index_name=search_index
        ),
        azure_openai=AzureOpenAIConfig(
            endpoint=openai_endpoint,
            api_key=openai_api_key,
            deployment_name=openai_deployment
        ),
        streamlit_port=streamlit_port
    )

