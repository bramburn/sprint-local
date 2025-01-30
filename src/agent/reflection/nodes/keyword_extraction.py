import logging
from typing import Dict
from langchain.text_splitter import RecursiveCharacterTextSplitter
from rake_nltk import Rake
from ..state.agent_state import AgentState

logger = logging.getLogger(__name__)

def extract_keywords(state: AgentState) -> Dict:
    """
    Extract keywords from the raw prompt using RAKE algorithm.
    
    Args:
        state: Current agent state
    
    Returns:
        Dict with extracted keywords
    """
    try:
        # Use RAKE for keyword extraction
        rake = Rake()
        rake.extract_keywords_from_text(state["raw_prompt"])
        
        # Get top 10 keywords by score
        keywords = rake.get_ranked_phrases_with_scores()
        top_keywords = [kw for _, kw in sorted(keywords, reverse=True)[:10]]
        
        # Fallback to text splitting if RAKE fails
        if not top_keywords:
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=50, 
                chunk_overlap=10
            )
            chunks = text_splitter.split_text(state["raw_prompt"])
            top_keywords = chunks[:10]
        
        logger.info(f"Extracted keywords: {top_keywords}")
        
        return {
            "keywords": top_keywords,
            "search_scope": 5  # Initial search scope
        }
    
    except Exception as e:
        logger.error(f"Error extracting keywords: {e}")
        return {
            "keywords": [state["raw_prompt"]],
            "search_scope": 3,
            "errors": [f"Keyword extraction failed: {e}"]
        }
