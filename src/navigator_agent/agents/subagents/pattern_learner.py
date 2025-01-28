import faiss
import numpy as np
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer

class PatternLearner:
    """
    Manages learning and retrieval of code repair patterns using FAISS vector store.
    """
    
    def __init__(
        self, 
        vector_store_path: str = "vector_store/repair_patterns",
        embedding_model: str = "all-MiniLM-L6-v2"
    ):
        """
        Initialize PatternLearner with embedding model and vector store.
        
        Args:
            vector_store_path (str): Path to store FAISS index
            embedding_model (str): Sentence transformer model for embeddings
        """
        self.embedding_model = SentenceTransformer(embedding_model)
        self.vector_store_path = vector_store_path
        
        try:
            # Try loading existing index
            self.index = faiss.read_index(f"{vector_store_path}/repair_patterns.index")
        except FileNotFoundError:
            # Create new index if not exists
            self.index = faiss.IndexFlatL2(self.embedding_model.get_sentence_embedding_dimension())
        
        self.pattern_metadata = []
    
    def add_repair_pattern(
        self, 
        original_code: str, 
        fixed_code: str, 
        error_type: str, 
        metadata: Dict[str, Any] = None
    ):
        """
        Add a new repair pattern to the vector store.
        
        Args:
            original_code (str): Code with error
            fixed_code (str): Corrected code
            error_type (str): Type of error fixed
            metadata (dict): Additional context about the repair
        """
        # Generate embeddings
        original_embedding = self.embedding_model.encode(original_code)
        fixed_embedding = self.embedding_model.encode(fixed_code)
        
        # Combine embeddings
        combined_embedding = np.concatenate([original_embedding, fixed_embedding])
        
        # Add to FAISS index
        self.index.add(np.array([combined_embedding]))
        
        # Store metadata
        pattern_info = {
            'original_code': original_code,
            'fixed_code': fixed_code,
            'error_type': error_type,
            'metadata': metadata or {}
        }
        self.pattern_metadata.append(pattern_info)
        
        # Periodically save index
        self._save_index()
    
    def find_similar_patterns(
        self, 
        code: str, 
        error_type: str = None, 
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Find similar repair patterns for given code.
        
        Args:
            code (str): Code to find similar patterns for
            error_type (str, optional): Filter by specific error type
            top_k (int): Number of similar patterns to return
        
        Returns:
            List of similar repair patterns
        """
        code_embedding = self.embedding_model.encode(code)
        
        # Search in vector store
        distances, indices = self.index.search(
            np.array([code_embedding]), 
            top_k
        )
        
        similar_patterns = []
        for idx in indices[0]:
            pattern = self.pattern_metadata[idx]
            
            # Optional error type filtering
            if error_type and pattern['error_type'] != error_type:
                continue
            
            similar_patterns.append(pattern)
        
        return similar_patterns
    
    def _save_index(self, save_frequency: int = 10):
        """
        Save FAISS index periodically.
        
        Args:
            save_frequency (int): Save every N additions
        """
        if len(self.pattern_metadata) % save_frequency == 0:
            faiss.write_index(
                self.index, 
                f"{self.vector_store_path}/repair_patterns.index"
            )
    
    def export_patterns(self, output_path: str = None):
        """
        Export learned repair patterns to a JSON file.
        
        Args:
            output_path (str, optional): Path to export patterns
        """
        import json
        
        output_path = output_path or f"{self.vector_store_path}/repair_patterns.json"
        
        with open(output_path, 'w') as f:
            json.dump(self.pattern_metadata, f, indent=2)

# Singleton pattern learner
pattern_learner = PatternLearner()
