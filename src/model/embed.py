from langchain_ollama import OllamaEmbeddings

from config import config

def get_ollama_embeddings():
    """Initialize and return Ollama embeddings with custom configuration"""
    return OllamaEmbeddings(
        model=config.OLLAMA_MODEL,
        base_url=config.OLLAMA_API_BASE,
       
    )
