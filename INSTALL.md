To implement the code search engine in your project, follow these steps:

## Setup

1. Install dependencies using Poetry:
```bash
poetry install
```

2. Set up your OpenAI API key in a `.env` file:
```
OPENAI_API_KEY=your_openai_api_key_here
```

## Implementation

### 1. Scan Repository

Use the `RepoScanner` class to scan your code repository:

```python
from scanner import RepoScanner

# Initialize scanner with your repository path
scanner = RepoScanner("/path/to/your/repository")

# Scan files
files = scanner.scan_files()
```

### 2. Create Vector Store

Use the `CodeVectorStore` class to create and populate the vector store:

```python
from vectorstore import CodeVectorStore

# Initialize vector store
vector_store = CodeVectorStore()

# Add scanned documents to the vector store
vector_store.add_documents([
    {"content": file_content, "metadata": file_metadata} 
    for file_content, file_metadata in files
])

# Optionally save the vector store for future use
vector_store.save("/path/to/store/index")
```

### 3. Perform Search

Use the `CodeSearch` class to search your codebase:

```python
from search import CodeSearch

# Initialize search engine with the vector store
search_engine = CodeSearch(vector_store)

# Perform a search
results = search_engine.search("find database connection method")

# Format and display results
for result in results:
    formatted_result = search_engine.format_result(result)
    print(f"File: {formatted_result['location']['file']}")
    print(f"Code: {formatted_result['code']}")
    print(f"Relevance: {formatted_result['relevance_score']}")
```

## Complete Workflow Example

Here's a complete example that ties everything together:

```python
from scanner import RepoScanner
from vectorstore import CodeVectorStore
from search import CodeSearch

def index_and_search_repository(repo_path, query):
    # 1. Scan repository
    scanner = RepoScanner(repo_path)
    files = scanner.scan_files()
    
    # 2. Create and populate vector store
    vector_store = CodeVectorStore()
    vector_store.add_documents([
        {"content": file['content'], "metadata": {
            "path": file['path'],
            "relative_path": file['relative_path']
        }} 
        for file in files
    ])
    
    # 3. Perform search
    search_engine = CodeSearch(vector_store)
    results = search_engine.search(query)
    
    # 4. Format and return results
    return [search_engine.format_result(result) for result in results]

# Usage
repo_path = "/path/to/your/repository"
search_query = "find database connection method"
search_results = index_and_search_repository(repo_path, search_query)

# Display results
for result in search_results:
    print(f"File: {result['location']['file']}")
    print(f"Code:\n{result['code']}")
    print(f"Relevance: {result['relevance_score']}")
    print("---")
```

This implementation allows you to scan your repository, create a searchable vector store of your code, and perform semantic searches across your codebase[1].

