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
        
        # Extract directory structure
        dir_structure = re.search(patterns['directory_structure'], xml_content, re.DOTALL)
        self.directory_structure = dir_structure.group(1).strip() if dir_structure else None
        
        # Extract file paths and contents
        files = {}
        for match in re.finditer(patterns['file_blocks'], xml_content, re.DOTALL):
            path, content = match.groups()
            files[path] = content.strip()
            
        return files
    
    def _construct_full_path(self, path: str, base_path: str = None) -> str:
        """Helper method to construct the full path"""
        return os.path.join(base_path, path) if base_path else path
    
    def process_files(self, files: Dict[str, str], base_path: str = None) -> List[str]:
        """Process and chunk file contents"""
        chunks = []
        for path, content in files.items():
            # Construct full path using helper method
            full_path = self._construct_full_path(path, base_path)
            metadata = {
                "source": path,
                "full_path": os.path.abspath(full_path)
            }
            file_chunks = self.text_splitter.create_documents([content], [metadata])
            chunks.extend(file_chunks)
        return chunks
    
    def process_directory_structure(self) -> List[str]:
        """Process directory structure into chunks"""
        if not self.directory_structure:
            return []
            
        metadata = {
            "type": "dir_structure",
            "source": "directory_structure"
        }
        return self.text_splitter.create_documents([self.directory_structure], [metadata])

    def create_vector_store(self, xml_path: str, output_dir: str, base_path: str = None) -> None:
        """Main method to create and save vector store"""
        with open(xml_path, 'r', encoding='utf-8') as f:
            xml_content = f.read()

        files = self.parse_xml(xml_content)
        chunks = self.process_files(files, base_path)
        dir_chunks = self.process_directory_structure()
        
        # Create and save FAISS index
        vector_store = FAISS.from_documents(chunks + dir_chunks, self.embeddings)
        os.makedirs(output_dir, exist_ok=True)
        vector_store.save_local(output_dir) 