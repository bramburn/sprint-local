import pytest
from unittest.mock import AsyncMock, Mock
from tools.navigator_tools import (
    NavigatorTools,
    ReflectionOutput,
    SolutionPlan,
    PlanSelectionOutput
)

@pytest.fixture
def mock_llm():
    llm = Mock()
    llm.agenerate = AsyncMock()
    return llm

@pytest.fixture
def navigator_tools(mock_llm):
    return NavigatorTools(mock_llm)

@pytest.mark.asyncio
async def test_generate_reflection(navigator_tools, mock_llm):
    # Setup
    problem_description = "Create a web scraper that extracts product information"
    mock_llm.agenerate.return_value = """
    Key Insights:
    - Need to handle different website structures
    - Rate limiting is important
    - Data validation required
    
    Edge Cases:
    - JavaScript rendered content
    - Anti-bot measures
    - Network failures
    
    Technical Considerations:
    - Choose appropriate HTTP client
    - Implement retry mechanism
    - Store data safely
    """
    
    # Execute
    result = await navigator_tools.generate_reflection(problem_description)
    
    # Assert
    assert isinstance(result, ReflectionOutput)
    assert len(result.insights) > 0
    assert len(result.edge_cases) > 0
    assert len(result.considerations) > 0
    mock_llm.agenerate.assert_called_once()

@pytest.mark.asyncio
async def test_generate_solution_plans(navigator_tools, mock_llm):
    # Setup
    problem_description = "Create a web scraper"
    reflection = ReflectionOutput(
        insights=["Need rate limiting"],
        edge_cases=["JavaScript content"],
        considerations=["Choose HTTP client"]
    )
    mock_llm.agenerate.return_value = """
    Plan 1:
    Title: Basic Requests-based Scraper
    Description: Simple synchronous scraper using requests
    Steps:
    - Setup requests session
    - Implement rate limiting
    Complexity: Low
    Risks:
    - Limited JavaScript support
    
    Plan 2:
    Title: Selenium-based Scraper
    Description: Full browser automation
    Steps:
    - Setup WebDriver
    - Handle dynamic content
    Complexity: Medium
    Risks:
    - Resource intensive
    """
    
    # Execute
    result = await navigator_tools.generate_solution_plans(problem_description, reflection)
    
    # Assert
    assert isinstance(result, list)
    assert len(result) > 0
    assert all(isinstance(plan, SolutionPlan) for plan in result)
    mock_llm.agenerate.assert_called_once()

@pytest.mark.asyncio
async def test_select_best_plan(navigator_tools, mock_llm):
    # Setup
    problem_description = "Create a web scraper"
    plans = [
        SolutionPlan(
            title="Basic Scraper",
            description="Simple synchronous scraper",
            steps=["Setup requests"],
            estimated_complexity="Low",
            potential_risks=["Limited JS support"]
        ),
        SolutionPlan(
            title="Advanced Scraper",
            description="Full browser automation",
            steps=["Setup Selenium"],
            estimated_complexity="Medium",
            potential_risks=["Resource intensive"]
        )
    ]
    mock_llm.agenerate.return_value = """
    Selected Plan: Basic Scraper
    Reasoning: Best balance of simplicity and functionality
    Alternative Considerations:
    - Could be extended later if needed
    - Easy to maintain
    """
    
    # Execute
    result = await navigator_tools.select_best_plan(problem_description, plans)
    
    # Assert
    assert isinstance(result, PlanSelectionOutput)
    assert isinstance(result.selected_plan, SolutionPlan)
    assert len(result.alternative_considerations) > 0
    mock_llm.agenerate.assert_called_once() 