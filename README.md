# Vector Store Management System

A Python-based system for managing vector stores and documentation using FAISS and LangChain.

## Features

- Add and manage documentation in vector stores
- Generate backlogs from prompts using LLM
- Execute LangChain interactions through CLI
- Efficient vector storage using FAISS
- Comprehensive documentation management

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-name>
```

2. Install dependencies using Poetry:
```bash
poetry install
```

## Quick Start

1. Add documentation to the vector store:
```bash
python cli_interface.py add-docs docs/example.md
```

2. Generate a backlog:
```bash
python cli_interface.py generate-backlog "Your project description" -o backlog.md
```

3. Use LangChain:
```bash
python cli_interface.py langchain --prompt "Your prompt"
```

## Documentation

For detailed usage instructions and examples, see:
- [CLI Usage Guide](docs/cli_usage.md)

## Project Structure

```
.
├── cli_interface.py        # CLI implementation
├── documentation.py        # Documentation management
├── vector_store_manager.py # Vector store operations
├── scanner.py             # File scanning utilities
├── docs/                  # Documentation
│   └── cli_usage.md       # CLI usage guide
└── tests/                 # Test files
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.