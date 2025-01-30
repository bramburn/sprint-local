import logging
import re
from typing import Dict, List, Optional, Union
from tenacity import retry, stop_after_attempt, wait_exponential

from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.exceptions import OutputParserException
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableConfig

# Import OpenRouter LLM
from src.llm.openrouter import get_openrouter

from ..state.agent_state import AgentState

logger = logging.getLogger(__name__)

# Structured output model for search queries with more detailed descriptions
class SearchQueries(BaseModel):
    """
    Structured representation of search queries generated from a task.
    """
    primary_query: str = Field(
        description="Main search query that best captures the core intent"
    )
    alternative_queries: List[str] = Field(
        default_factory=list,
        description="Alternative phrasings or related queries"
    )
    search_scope: str = Field(
        default="all",
        description="Suggested scope for the search (e.g., 'all', 'python', 'tests')"
    )
    query_details: Dict[str, str] = Field(
        default_factory=dict,
        description="Additional details about each query's purpose"
    )

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
def extract_keywords(state: Union[Dict, AgentState]) -> Dict:
    """
    Generate search queries using an LLM with structured output and robust error handling.
    
    Args:
        state: Current agent state containing the raw prompt (can be Dict or AgentState)
    
    Returns:
        Dict with generated search queries, search scope, and query details
    
    Raises:
        OutputParserException: When structured output parsing fails
        ValueError: When primary query generation fails
    """
    # Get the raw prompt from state
    raw_prompt = state.raw_prompt if isinstance(state, AgentState) else state.get("raw_prompt")
    
    if not raw_prompt:
        raise ValueError("No raw prompt found in state")
    
    # Initialize the LLM
    llm = get_openrouter()
    
    # Create output parser
    parser = PydanticOutputParser(pydantic_object=SearchQueries)
    
    # Define prompt template
    template = """Given the following task or question, generate search queries that will help find relevant information.
    Focus on extracting key technical terms and concepts.

    Task: {raw_prompt}

    Generate a structured response that includes:
    1. A primary search query that best captures the core intent
    2. Alternative phrasings or related queries
    3. Suggested scope for the search (e.g., 'all', 'python', 'tests')
    4. Brief details about each query's purpose

    {format_instructions}
    """
    
    # Create prompt with format instructions
    prompt = PromptTemplate(
        template=template,
        input_variables=["raw_prompt"],
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    
    try:
        # Generate queries using LLM
        llm_output = llm.invoke(
            prompt.format_prompt(raw_prompt=raw_prompt),
            config=RunnableConfig(callbacks=None)
        )
        
        # Parse structured output
        parsed_output = parser.parse(llm_output)
        
        # Convert to dict and add metadata
        result = parsed_output.model_dump()
        result["success"] = True
        result["error"] = None
        
        return result
        
    except OutputParserException as e:
        logger.error(f"Failed to parse LLM output: {str(e)}")
        # Fallback to simple keyword extraction
        keywords = re.findall(r'\w+', raw_prompt.lower())
        return {
            "success": False,
            "error": str(e),
            "primary_query": " ".join(keywords[:3]),
            "alternative_queries": [],
            "search_scope": "all",
            "query_details": {}
        }
        
    except Exception as e:
        logger.error(f"Error in keyword extraction: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "primary_query": raw_prompt[:50],
            "alternative_queries": [],
            "search_scope": "all",
            "query_details": {}
        }
