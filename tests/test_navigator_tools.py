import pytest
from unittest.mock import AsyncMock, Mock
from tools.navigator_tools import (
    NavigatorTools, RefinedProblem, RiskAssessment, PlanEvaluation,
    ArchitectureDecision, TechnicalConstraint
)

@pytest.fixture
def mock_llm():
    llm = Mock()
    llm.aask = AsyncMock()
    llm.parse_json = Mock()
    return llm

@pytest.fixture
def navigator_tools(mock_llm):
    return NavigatorTools(mock_llm)

@pytest.mark.asyncio
async def test_refine_problem(navigator_tools, mock_llm):
    # Setup mock response
    mock_llm.parse_json.return_value = {
        "refined_description": "A detailed problem description",
        "clarifications": ["What is the expected scale?", "What are the performance requirements?"],
        "requirements": ["Must handle high load", "Must be secure"]
    }
    
    # Test the method
    result = await navigator_tools.refine_problem("Build a web service")
    
    # Verify the result
    assert isinstance(result, RefinedProblem)
    assert result.original_description == "Build a web service"
    assert result.refined_description == "A detailed problem description"
    assert len(result.clarifications) == 2
    assert len(result.requirements) == 2
    
    # Verify LLM was called correctly
    mock_llm.aask.assert_called_once()
    assert "Build a web service" in mock_llm.aask.call_args[0][0]

@pytest.mark.asyncio
async def test_analyze_risks(navigator_tools, mock_llm):
    # Setup mock response
    mock_llm.parse_json.return_value = [{
        "risk_name": "Performance Bottleneck",
        "severity": "High",
        "probability": "Medium",
        "impact": "System slowdown under load",
        "mitigation_strategy": "Implement caching"
    }]
    
    # Test the method
    result = await navigator_tools.analyze_risks("Use a monolithic architecture")
    
    # Verify the result
    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], RiskAssessment)
    assert result[0].risk_name == "Performance Bottleneck"
    assert result[0].severity == "High"
    assert result[0].probability == "Medium"
    
    # Verify LLM was called correctly
    mock_llm.aask.assert_called_once()
    assert "monolithic architecture" in mock_llm.aask.call_args[0][0]

@pytest.mark.asyncio
async def test_compare_plans(navigator_tools, mock_llm):
    # Setup test data
    plans = [
        {"plan_id": "1", "plan_description": "Monolithic approach"},
        {"plan_id": "2", "plan_description": "Microservices approach"}
    ]
    
    # Setup mock response
    mock_llm.parse_json.return_value = [{
        "plan_id": "1",
        "score": 7.5,
        "strengths": ["Simple to implement"],
        "weaknesses": ["Limited scalability"],
        "reasoning": "Good for small scale"
    }, {
        "plan_id": "2",
        "score": 8.5,
        "strengths": ["Highly scalable"],
        "weaknesses": ["Complex deployment"],
        "reasoning": "Better for long term"
    }]
    
    # Test the method
    result = await navigator_tools.compare_plans(plans)
    
    # Verify the result
    assert isinstance(result, list)
    assert len(result) == 2
    assert isinstance(result[0], PlanEvaluation)
    assert result[0].plan_id == "1"
    assert result[0].score == 7.5
    assert len(result[0].strengths) == 1
    assert len(result[0].weaknesses) == 1
    
    # Verify LLM was called correctly
    mock_llm.aask.assert_called_once()
    assert "Monolithic approach" in mock_llm.aask.call_args[0][0]
    assert "Microservices approach" in mock_llm.aask.call_args[0][0]

@pytest.mark.asyncio
async def test_refine_problem_invalid_response(navigator_tools, mock_llm):
    # Setup mock to raise an exception
    mock_llm.parse_json.side_effect = ValueError("Invalid JSON")
    
    # Test the method raises an exception
    with pytest.raises(ValueError) as exc_info:
        await navigator_tools.refine_problem("Build a web service")
    
    assert "Failed to parse LLM response" in str(exc_info.value)

@pytest.mark.asyncio
async def test_analyze_risks_invalid_response(navigator_tools, mock_llm):
    # Setup mock to raise an exception
    mock_llm.parse_json.side_effect = ValueError("Invalid JSON")
    
    # Test the method raises an exception
    with pytest.raises(ValueError) as exc_info:
        await navigator_tools.analyze_risks("Use a monolithic architecture")
    
    assert "Failed to parse LLM response" in str(exc_info.value)

@pytest.mark.asyncio
async def test_compare_plans_invalid_response(navigator_tools, mock_llm):
    # Setup test data
    plans = [
        {"plan_id": "1", "plan_description": "Monolithic approach"},
        {"plan_id": "2", "plan_description": "Microservices approach"}
    ]
    
    # Setup mock to raise an exception
    mock_llm.parse_json.side_effect = ValueError("Invalid JSON")
    
    # Test the method raises an exception
    with pytest.raises(ValueError) as exc_info:
        await navigator_tools.compare_plans(plans)
    
    assert "Failed to parse LLM response" in str(exc_info.value)

@pytest.mark.asyncio
async def test_identify_constraints(navigator_tools, mock_llm):
    # Setup mock response
    mock_llm.parse_json.return_value = [{
        "constraint_type": "Performance",
        "description": "Must handle 1000 requests per second",
        "impact": "High load on database",
        "mitigation_options": ["Use caching", "Optimize queries"]
    }]
    
    # Test the method
    result = await navigator_tools.identify_constraints("Build a high-traffic web service")
    
    # Verify the result
    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], TechnicalConstraint)
    assert result[0].constraint_type == "Performance"
    assert len(result[0].mitigation_options) == 2
    
    # Verify LLM was called correctly
    mock_llm.aask.assert_called_once()
    assert "high-traffic web service" in mock_llm.aask.call_args[0][0]

@pytest.mark.asyncio
async def test_make_architecture_decision(navigator_tools, mock_llm):
    # Setup test data
    constraints = [
        TechnicalConstraint(
            constraint_type="Performance",
            description="High load",
            impact="System responsiveness",
            mitigation_options=["Caching"]
        )
    ]
    
    # Setup mock response
    mock_llm.parse_json.return_value = {
        "decision": "Use microservices architecture",
        "context": "High scalability requirements",
        "consequences": ["Better scalability", "More complex deployment"],
        "alternatives": ["Monolithic", "Serverless"],
        "rationale": "Best fits scalability needs"
    }
    
    # Test the method
    result = await navigator_tools.make_architecture_decision(
        "Build a scalable system",
        constraints
    )
    
    # Verify the result
    assert isinstance(result, ArchitectureDecision)
    assert result.decision == "Use microservices architecture"
    assert len(result.consequences) == 2
    assert len(result.alternatives) == 2
    
    # Verify LLM was called correctly
    mock_llm.aask.assert_called_once()
    assert "scalable system" in mock_llm.aask.call_args[0][0]
    assert "Performance" in mock_llm.aask.call_args[0][0]

@pytest.mark.asyncio
async def test_validate_solution_completeness(navigator_tools, mock_llm):
    # Setup test data
    problem = "Build a user authentication system"
    solution = "Implement OAuth2 with JWT tokens"
    requirements = ["Secure password storage", "2FA support"]
    
    # Setup mock response
    mock_llm.parse_json.return_value = {
        "covered_requirements": ["Secure password storage"],
        "missing_aspects": ["2FA implementation details"],
        "implementation_gaps": ["Token refresh mechanism"],
        "unhandled_edge_cases": ["Password reset flow"],
        "completeness_score": 0.7,
        "recommendations": ["Add 2FA implementation"]
    }
    
    # Test the method
    result = await navigator_tools.validate_solution_completeness(
        problem,
        solution,
        requirements
    )
    
    # Verify the result
    assert isinstance(result, dict)
    assert "covered_requirements" in result
    assert "completeness_score" in result
    assert result["completeness_score"] == 0.7
    
    # Verify LLM was called correctly
    mock_llm.aask.assert_called_once()
    assert "OAuth2" in mock_llm.aask.call_args[0][0]
    assert "2FA support" in mock_llm.aask.call_args[0][0]

@pytest.mark.asyncio
async def test_estimate_implementation_effort(navigator_tools, mock_llm):
    # Setup test data
    solution = "Build a microservices-based e-commerce system"
    team_context = {
        "size": 5,
        "experience": "Medium",
        "tech_stack": ["Python", "React"]
    }
    
    # Setup mock response
    mock_llm.parse_json.return_value = {
        "overall_complexity": "High",
        "total_effort_days": 120,
        "required_skills": ["Python", "Microservices", "DevOps"],
        "risk_factors": ["Team's first microservices project"],
        "phase_breakdown": {
            "design": 20,
            "implementation": 60,
            "testing": 25,
            "deployment": 15
        }
    }
    
    # Test the method
    result = await navigator_tools.estimate_implementation_effort(
        solution,
        team_context
    )
    
    # Verify the result
    assert isinstance(result, dict)
    assert result["overall_complexity"] == "High"
    assert result["total_effort_days"] == 120
    assert "phase_breakdown" in result
    
    # Verify LLM was called correctly
    mock_llm.aask.assert_called_once()
    assert "microservices" in mock_llm.aask.call_args[0][0]
    assert "Python" in mock_llm.aask.call_args[0][0]

@pytest.mark.asyncio
async def test_identify_constraints_invalid_response(navigator_tools, mock_llm):
    # Setup mock to raise an exception
    mock_llm.parse_json.side_effect = ValueError("Invalid JSON")
    
    # Test the method raises an exception
    with pytest.raises(ValueError) as exc_info:
        await navigator_tools.identify_constraints("Build a system")
    
    assert "Failed to parse LLM response" in str(exc_info.value)

@pytest.mark.asyncio
async def test_make_architecture_decision_invalid_response(navigator_tools, mock_llm):
    # Setup mock to raise an exception
    mock_llm.parse_json.side_effect = ValueError("Invalid JSON")
    
    # Test the method raises an exception
    with pytest.raises(ValueError) as exc_info:
        await navigator_tools.make_architecture_decision(
            "Build a system",
            []
        )
    
    assert "Failed to parse LLM response" in str(exc_info.value)

@pytest.mark.asyncio
async def test_validate_solution_completeness_invalid_response(navigator_tools, mock_llm):
    # Setup mock to raise an exception
    mock_llm.parse_json.side_effect = ValueError("Invalid JSON")
    
    # Test the method raises an exception
    with pytest.raises(ValueError) as exc_info:
        await navigator_tools.validate_solution_completeness(
            "problem",
            "solution",
            ["req1"]
        )
    
    assert "Failed to parse LLM response" in str(exc_info.value)

@pytest.mark.asyncio
async def test_estimate_implementation_effort_invalid_response(navigator_tools, mock_llm):
    # Setup mock to raise an exception
    mock_llm.parse_json.side_effect = ValueError("Invalid JSON")
    
    # Test the method raises an exception
    with pytest.raises(ValueError) as exc_info:
        await navigator_tools.estimate_implementation_effort("Build a system")
    
    assert "Failed to parse LLM response" in str(exc_info.value) 