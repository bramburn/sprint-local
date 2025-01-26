import os
from pathlib import Path
from typing import List, Dict, Any
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from config import config

def load_vector_store(vector_store_location: str) -> FAISS:
    """
    Load a vector store from the specified location.
    
    Args:
        vector_store_location (str): Path to the vector store to load
        
    Returns:
        FAISS: Loaded vector store instance
        
    Raises:
        FileNotFoundError: If vector store directory doesn't exist
        RuntimeError: If vector store fails to load
    """
    # Validate vector store location
    if not Path(vector_store_location).exists():
        raise FileNotFoundError(f"Vector store directory not found: {vector_store_location}")

    # Initialize embeddings with config API key
    embeddings = OpenAIEmbeddings(
        api_key=config.openai_key,
        model=config.embedding_model
    )
    
    try:
        # Load the FAISS index with safety flag
        vector_store = FAISS.load_local(
            vector_store_location, 
            embeddings, 
            allow_dangerous_deserialization=True
        )
        return vector_store
    except Exception as e:
        raise RuntimeError(f"Failed to load vector store: {str(e)}")

def search_vector_store(vector_store: FAISS, query: str, k: int = 6) -> List[Dict[str, Any]]:
    """
    Perform a search on the loaded vector store.
    
    Args:
        vector_store (FAISS): Loaded vector store instance
        query (str): Search query
        k (int): Number of results to return
        
    Returns:
        List[Dict[str, Any]]: Search results with metadata
    """
    results = vector_store.similarity_search_with_score(query, k=k)
    
    return [{
        'content': result.page_content,
        'score': score,
        'metadata': result.metadata,
        'file_path': result.metadata.get('file_path', 'Unknown')
    } for result, score in results]

def main():
    try:
        # Load vector store from configured location
        vector_store_location = os.path.join(
            os.path.dirname(__file__), 
            'vector_store','current'
        )
        vector_store = load_vector_store(vector_store_location)
        
        print("Vector store loaded successfully. Enter search queries below:")
        
        while True:
            query = input("\nEnter your search query (or 'exit' to quit): ").strip()
            if query.lower() == 'exit':
                break
                
            if not query:
                print("Please enter a valid query.")
                continue
                
            # Perform search and display results
            results = search_vector_store(vector_store, query)
            
            if not results:
                print("No results found.")
                continue
                
            for i, result in enumerate(results, 1):
                print(f"\nResult {i}:")
                print(f"File: {result['file_path']}")
                print(f"Score: {result['score']:.2f}")
                
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 