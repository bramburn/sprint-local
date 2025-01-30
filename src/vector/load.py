import os
from langchain_community.vectorstores import FAISS
from src.model.embed import get_ollama_embeddings

def load_vector_store(vector_dir: str):
    """Load FAISS vector store from specified directory"""
    embeddings = get_ollama_embeddings()
    return FAISS.load_local(vector_dir, embeddings, allow_dangerous_deserialization=True) 

def load_vector_store_by_name(vector_name: str):
    """Load FAISS vector store from specified directory"""
    try:
        vector_dir = os.path.join(os.path.dirname(__file__), "..", "..", "vector_store", vector_name)
        if not os.path.exists(vector_dir):
            raise FileNotFoundError(f"Directory {vector_dir} does not exist.")
    except FileNotFoundError as e:
        print(f"Error loading vector store: {e}")
        return None
    embeddings = get_ollama_embeddings()
    return FAISS.load_local(vector_dir, embeddings, allow_dangerous_deserialization=True) 
