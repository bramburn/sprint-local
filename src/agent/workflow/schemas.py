from pydantic import BaseModel, Field
from typing import List
from src.decorators.structured_output import structured_output
from langchain_core.messages.ai import AIMessage
class DirectoryStructureInformation(BaseModel):
    framework: str = Field(
        description="Explanation of the directory structure's potential framework"
    )
    modules: List[str] = Field(
        description="List of potential different modules or components identified in the directory structure"
    )
    settings_file: str = Field(description="Path to potential settings file")
    configuration_file: str = Field(description="Path to potential configuration file")
    explanation: str = Field(
        description="Explanation of how you came to understand the directory structure"
    )

class SearchQuery(BaseModel):
    queries: List[str] = Field(default_factory=list, description="List of search queries to find relevant files")

@structured_output(
    pydantic_model=SearchQuery,  
    max_retries=3
)
def parse_search_queries(data:str):

    prompt=  f"""
    I am going to provide you some data to process:
    ```text
    {data}
    ```
    I want you to now return it into a structured format.
    """
    
    return prompt
