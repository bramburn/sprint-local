from langchain_ollama import OllamaLLM
from config import config


# gemma2:latest

def get_ollama(model: str = "deepseek-r1:latest", max_tokens: int = 8192, temperature: float = 0.7) -> OllamaLLM:
    return OllamaLLM(
        model=model,
        max_tokens=max_tokens,
        max_retries=10,
        base_url="http://localhost:10000",
        temperature=temperature
    )
