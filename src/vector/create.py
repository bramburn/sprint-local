import re
import os
from typing import List, Dict
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from src.model.embed import get_ollama_embeddings

class XMLVectorCreator:
    def __init__(self):
        self.embeddings = get_ollama_embeddings()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        
    def parse_xml(self, xml_content: str) -> Dict[str, str]:
        """Parse the XML-like content using regex"""
        patterns = {
            'directory_structure': r'<directory_structure>(.*?)</directory_structure>',
            'file_blocks': r'<file path="(.*?)">(.*?)</file>'
        }
        
        # Extract file paths and contents
        files = {}
        for match in re.finditer(patterns['file_blocks'], xml_content, re.DOTALL):
            path, content = match.groups()
            files[path] = content.strip()
            
        return files
    
    def process_files(self, files: Dict[str, str]) -> List[str]:
        """Process and chunk file contents"""
        chunks = []
        for path, content in files.items():
            # Add path as metadata
            metadata = {"source": path}
            file_chunks = self.text_splitter.create_documents([content], [metadata])
            chunks.extend(file_chunks)
        return chunks
    
    def create_vector_store(self, xml_path: str, output_dir: str) -> None:
        """Main method to create and save vector store"""
        # Read and parse XML
        with open(xml_path, 'r', encoding='utf-8') as f:
            xml_content = f.read()
        
        files = self.parse_xml(xml_content)
        chunks = self.process_files(files)
        
        # Create and save FAISS index
        vector_store = FAISS.from_documents(chunks, self.embeddings)
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        vector_store.save_local(output_dir) 