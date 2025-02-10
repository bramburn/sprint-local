from langchain_ollama import OllamaLLM
from config import config


# gemma2:latest
# http://192.168.0.49:10000
# http://localhost:10000
def get_ollama(model: str = "deepseek-r1:latest", max_tokens: int = 8192, temperature: float = 0.7,base_url: str = "http://192.168.0.49:10000") -> OllamaLLM:
    return OllamaLLM(
        model=model,
        max_tokens=max_tokens,
        max_retries=10,
        base_url=base_url,
        temperature=temperature
    )
