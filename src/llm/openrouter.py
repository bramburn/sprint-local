from langchain_openai import ChatOpenAI
from config import config

def get_openrouter(model: str = "meta-llama/llama-3.2-3b-instruct") -> ChatOpenAI:
    return ChatOpenAI(
        model=model,
        openai_api_key=config.OPENROUTER_API_KEY,
        openai_api_base=config.OPENROUTER_API_BASE,
        max_retries=3
    ) 