from pathlib import Path
from config import Config
from scanner import RepoScanner
from vectorstore import CodeVectorStore

def validate_path(path: str, path_type: str) -> Path:
    """
    Validate if a path exists and return it as a Path object.
    
    Args:
        path (str): Path to validate
        path_type (str): Description of the path for error messages
        
    Returns:
        Path: Validated path as Path object
        
    Raises:
        FileNotFoundError: If path does not exist
    """
    path = Path(path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"{path_type} does not exist: {path}")
    return path

def initialize_vector_store(vector_store_location: str, repo_folder: str) -> None:
    """
    Initialize and save a vector store with JavaScript files from a repository.
    
    Args:
        vector_store_location (str): Path to save the vector store
        repo_folder (str): Path to the repository to scan
        
    Raises:
        FileNotFoundError: If repository folder does not exist
        ValueError: If no JavaScript files are found in the repository
    """
    # Validate paths
    repo_path = validate_path(repo_folder, "Repository folder")
    vector_store_path = Path(vector_store_location).resolve()
    
    # Initialize the RepoScanner with the repository path
    scanner = RepoScanner(str(repo_path))
    scanner.set_inclusion_patterns(['*.js', '*.ts', '*.tsx', '*.jsx'])  # Include only .js files
    scanner.set_ignore_list(['node_modules/','*.test.ts'])
    
    # Scan for files
    scanned_files = scanner.scan_files()
    
    if not scanned_files:
        raise ValueError("No JavaScript files found in the repository")
    # for file in scanned_files:
    #     print(f"File Path: {file['metadata']['file_path']}, Size: {file['metadata']['file_size']} bytes")
    #     relative_path = file['metadata']['relative_path']
    #     print(f"Relative File Path: {relative_path}")
    # Initialize the CodeVectorStore with configuration
    config = Config()
    vector_store = CodeVectorStore(
        storage_path=str(vector_store_path),
        embedding_model=config.embedding_model,
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap
    )
    
    # # Add scanned documents to the vector store with repository path
    vector_store.add_documents(
        [{"content": file['content'], "metadata": file['metadata']} for file in scanned_files],
        repo_path=repo_path
    )
    
    # # Save the vector store
    vector_store.save()
    print(f"Vector store successfully created and saved at: {vector_store_path}")

def main():
    try:
        # Get user input for paths
        # vector_store_location = input("Enter the vector store location: ").strip()
        vector_store_location = "C:/dev/sprint_app/sprint-py/vector_store/code/"
        repo_folder = "C:/dev/repomix"
        
        # Initialize and save the vector store
        initialize_vector_store(vector_store_location, repo_folder)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        exit(1)

if __name__ == "__main__":
    main() 