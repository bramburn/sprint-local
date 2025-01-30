from langchain_openai import ChatOpenAI
from config import config

def get_openrouter(model: str = "meta-llama/llama-3.2-3b-instruct",max_tokens:int=8192) -> ChatOpenAI:
    return ChatOpenAI(
        model=model,
        openai_api_key=config.OPENROUTER_API_KEY,
        openai_api_base=config.OPENROUTER_API_BASE,
        max_retries=3,
        max_tokens=max_tokens
    ) 