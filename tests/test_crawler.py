import asyncio
import logging
import os
import pytest
from typing import List, Dict, Optional

from src.agent.workflow.crawler import WebResearchCrawler, SearchQuery

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def is_service_available() -> bool:
    """
    Check if required services are available.
    
    Returns:
        bool: True if services are available, False otherwise
    """
    try:
        import requests
        # Check Ollama service
        ollama_response = requests.get("http://localhost:10000/api/tags", timeout=3)
        return ollama_response.status_code == 200
    except Exception:
        return False

def test_search_query_model():
    """
    Test the SearchQuery Pydantic model validation.
    """
    from pydantic import ValidationError
    
    # Valid queries
    valid_queries = [
        "Machine learning techniques in modern AI",
        "Advanced neural network architectures",
        "Quantum computing breakthrough research",
        "the comprehensive analysis of AI technologies",  # This should now pass
        "AI"  # This should now pass
    ]
    
    # Invalid queries to test validation
    invalid_queries = [
        "",  # Empty string
        "a",  # Forbidden word
        "an"  # Forbidden word
    ]
    
    # Test valid queries
    for query_text in valid_queries:
        query = SearchQuery(query=query_text)
        assert query.query == query_text, f"Valid query {query_text} should be accepted"
    
    # Test invalid queries
    for query_text in invalid_queries:
        with pytest.raises(ValidationError, match="Query must contain meaningful keywords"):
            SearchQuery(query=query_text)

@pytest.mark.skipif(not is_service_available(), reason="Ollama service not running")
def test_query_generation_mock():
    """
    Test query generation and web search with a mock crawler.
    """
    # Create a mock crawler with minimal dependencies
    crawler = WebResearchCrawler()
    
    # Test scenarios with more detailed queries
    test_questions = [
        "Explain advanced machine learning algorithms in modern AI",
        "Latest technological trends in artificial intelligence research",
        "Comprehensive overview of climate change impact on global ecosystems"
    ]
    
    for question in test_questions:
        # Generate queries
        queries = crawler.generate_search_queries(question)
        
        # Validate queries
        assert isinstance(queries, list), "Queries should be a list"
        assert len(queries) > 0, "At least one query should be generated"
        
        # Validate each SearchQuery object
        for query in queries:
            assert isinstance(query, SearchQuery), "Each query should be a SearchQuery object"
            assert len(query.query) > 0, "Query should not be empty"
            assert query.query != question, "Query should not be identical to original question"
            
            # Optional intent validation
            if query.intent:
                assert isinstance(query.intent, str), "Intent should be a string"
                assert len(query.intent) > 0, "Intent should not be empty"
        
        # Perform web search
        search_results = crawler.search_web([q.query for q in queries])
        
        # Validate search results
        assert isinstance(search_results, list), "Search results should be a list"
        assert len(search_results) > 0, "At least one search result should be returned"
        
        # Validate each search result
        for result in search_results:
            assert isinstance(result, dict), "Each search result should be a dictionary"
            assert "title" in result, "Search result missing title"
            assert "href" in result, "Search result missing href"
            assert "body" in result, "Search result missing body"
            assert "query" in result, "Search result missing original query"
            assert "metadata" in result, "Search result missing metadata"
            
            # Validate metadata
            assert isinstance(result["metadata"], dict), "Metadata should be a dictionary"
            assert "region" in result["metadata"], "Metadata missing region"
            assert "safesearch" in result["metadata"], "Metadata missing safesearch"

def test_crawler_initialization():
    """
    Test basic crawler initialization.
    """
    try:
        crawler = WebResearchCrawler()
        
        # Check for essential attributes
        essential_attrs = [
            'logger', 
            'ddgs', 
            'async_crawler', 
            'sync_crawler'
        ]
        
        for attr in essential_attrs:
            assert hasattr(crawler, attr), f"Crawler missing {attr} attribute"
        
        # Optional: Additional type checks
        assert hasattr(crawler.logger, 'info'), "Logger should have info method"
    
    except Exception as e:
        logger.error(f"Crawler initialization test failed: {e}")
        pytest.fail(f"Crawler initialization test failed: {e}")

# Placeholder for potential async tests that require external services
@pytest.mark.skipif(not is_service_available(), reason="Ollama service not running")
def test_async_research_placeholder():
    """
    Placeholder for async research tests.
    This test will be skipped if Ollama service is not available.
    """
    assert True, "Placeholder for future async research tests"
