from langchain_community.vectorstores import FAISS
from src.model.embed import get_ollama_embeddings

def load_vector_store(vector_dir: str):
    """Load FAISS vector store from specified directory"""
    embeddings = get_ollama_embeddings()
    return FAISS.load_local(vector_dir, embeddings, allow_dangerous_deserialization=True) 