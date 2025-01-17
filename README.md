# Code Search Engine

## Overview

This project provides a comprehensive code search and analysis tool that allows you to:
- Scan code repositories
- Extract code structure
- Create vector embeddings
- Perform semantic code searches

## Components

### 1. Repository Scanner (`scanner.py`)
Scans and processes code files in a repository, respecting `.gitignore` rules.

#### Usage Example:
```python
from scanner import RepoScanner

# Scan a repository
scanner = RepoScanner("/path/to/your/repository")
files = scanner.scan_files()
```

### 2. Vector Store (`vectorstore.py`)
Manages code embeddings and vector storage using OpenAI embeddings and FAISS.

#### Usage Example:
```python
from vectorstore import CodeVectorStore
from scanner import RepoScanner

# Initialize vector store
vector_store = CodeVectorStore()

# Scan repository and add documents
scanner = RepoScanner("/path/to/your/repository")
files = scanner.scan_files()

# Process and store code files
vector_store.add_documents([
    {"content": file_content, "metadata": file_metadata} 
    for file_content, file_metadata in files
])

# Optionally save the vector store
vector_store.save("/path/to/store/index")
```

### 3. Code Analyzer (`code_analyzer.py`)
Extracts structural information from code files.

#### Usage Example:
```python
from code_analyzer import CodeAnalyzer

analyzer = CodeAnalyzer()
file_structure = analyzer.analyze("/path/to/your/file.py")
```

### 4. Search Engine (`search.py`)
Perform semantic searches across your codebase.

#### Usage Example:
```python
from vectorstore import CodeVectorStore
from search import CodeSearch

# Load or create vector store
vector_store = CodeVectorStore()
vector_store.load("/path/to/stored/index")  # Optional: load existing index

# Initialize search
search_engine = CodeSearch(vector_store)

# Perform search
results = search_engine.search("find function that calculates tax")

# Format and display results
for result in results:
    formatted_result = search_engine.format_result(result)
    print(f"File: {formatted_result['location']['file']}")
    print(f"Code: {formatted_result['code']}")
    print(f"Relevance: {formatted_result['relevance_score']}")
```

## Complete Workflow Example

```python
from scanner import RepoScanner
from vectorstore import CodeVectorStore
from search import CodeSearch

def index_and_search_repository(repo_path):
    # 1. Scan repository
    scanner = RepoScanner(repo_path)
    files = scanner.scan_files()
    
    # 2. Create vector store
    vector_store = CodeVectorStore()
    vector_store.add_documents([
        {"content": file_content, "metadata": file_metadata} 
        for file_content, file_metadata in files
    ])
    
    # 3. Save vector index (optional)
    vector_store.save("/path/to/store/index")
    
    # 4. Perform search
    search_engine = CodeSearch(vector_store)
    results = search_engine.search("find database connection method")
    
    return results

# Usage
results = index_and_search_repository("/path/to/your/repository")
```

## Configuration

1. Set up your OpenAI API key in `.env`:
```
OPENAI_API_KEY=your_openai_api_key_here
```

## Dependencies

- Install dependencies using Poetry:
```bash
poetry install
```

## Testing

Run tests using:
```bash
poetry run pytest
```

## Limitations

- Requires OpenAI API access
- Performance depends on embedding model
- Large repositories may take time to index

## Contributing

Contributions are welcome! Please submit pull requests or open issues on our repository.

## License

[Your License Here]