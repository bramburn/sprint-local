import pandas as pd
from typing import Dict, Any, List
import numpy as np
from scipy.spatial.distance import cosine

class Store:
    """
    A scalable and efficient store for code metadata and document chunks.
    """
    def __init__(self, repo_path: str = None):
        """
        Initialize the store with an optional repository path.

        Args:
            repo_path (str, optional): Path to the repository. Defaults to None.
        """
        self.metadata_df = pd.DataFrame(columns=[
            'file_path', 'type', 'name', 'line', 
            'docstring', 'embedding', 'additional_info'
        ])
        self.repo_path = repo_path

    def add_metadata(self, metadata: Dict[str, Any], file_path: str):
        """
        Add metadata to the store.

        Args:
            metadata (Dict[str, Any]): Metadata to be added.
            file_path (str): Path of the file being analyzed.
        """
        # Process functions
        for func in metadata.get('functions', []):
            self.metadata_df = self.metadata_df.append({
                'file_path': file_path,
                'type': 'function',
                'name': func.get('name', ''),
                'line': func.get('line', 0),
                'docstring': func.get('docstring', ''),
                'embedding': self._generate_embedding(func.get('docstring', '')),
                'additional_info': {
                    'args': func.get('args', []),
                    'is_async': func.get('is_async', False)
                }
            }, ignore_index=True)

        # Process classes
        for cls in metadata.get('classes', []):
            self.metadata_df = self.metadata_df.append({
                'file_path': file_path,
                'type': 'class',
                'name': cls.get('name', ''),
                'line': cls.get('line', 0),
                'docstring': cls.get('docstring', ''),
                'embedding': self._generate_embedding(cls.get('docstring', '')),
                'additional_info': {
                    'methods': cls.get('methods', [])
                }
            }, ignore_index=True)

    def _generate_embedding(self, text: str) -> np.ndarray:
        """
        Generate a simple embedding for text using character-level representation.

        Args:
            text (str): Text to generate embedding for.

        Returns:
            np.ndarray: Embedding vector.
        """
        # Simple embedding: character count and unique character distribution
        if not text:
            return np.zeros(10)
        
        char_counts = [text.count(chr(i)) for i in range(97, 107)]  # a-j
        return np.array(char_counts)

    def similarity_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Perform similarity search on stored metadata.

        Args:
            query (str): Search query.
            top_k (int, optional): Number of top results to return. Defaults to 5.

        Returns:
            List[Dict[str, Any]]: Top similar metadata entries.
        """
        query_embedding = self._generate_embedding(query)
        
        # Calculate cosine similarity
        self.metadata_df['similarity'] = self.metadata_df['embedding'].apply(
            lambda x: 1 - cosine(x, query_embedding)
        )
        
        # Sort and return top results
        return (self.metadata_df.sort_values('similarity', ascending=False)
                .head(top_k)
                .to_dict('records'))

    def save(self, storage_path: str = None):
        """
        Save the metadata store to a specified path.

        Args:
            storage_path (str, optional): Path to save the metadata. 
                                          Defaults to None (uses repo_path).
        """
        if storage_path is None:
            storage_path = self.repo_path or './metadata_store.parquet'
        
        self.metadata_df.to_parquet(storage_path)

    def load(self, storage_path: str = None):
        """
        Load metadata from a specified path.

        Args:
            storage_path (str, optional): Path to load the metadata from. 
                                          Defaults to None (uses repo_path).
        """
        if storage_path is None:
            storage_path = self.repo_path or './metadata_store.parquet'
        
        self.metadata_df = pd.read_parquet(storage_path)
