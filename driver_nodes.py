import logging
from typing import Dict, Any
import ast
import re
from models import DriverState, PlanInfo, StaticAnalysisResult, TestResult

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_plan(plan: str) -> PlanInfo:
    """
    Analyze the selected plan to extract key information.
    
    Args:
        plan (str): The selected plan
    
    Returns:
        PlanInfo: Extracted information including function name, parameters, etc.
    """
    # Extract function name using regex
    func_name_match = re.search(r'implement\s+(?:a\s+)?(?:function\s+)?([a-zA-Z_][a-zA-Z0-9_]*)', plan.lower())
    func_name = func_name_match.group(1) if func_name_match else 'generated_function'
    
    # Extract parameters if specified
    param_match = re.search(r'with\s+parameters?\s+([^\.]+)', plan.lower())
    params = param_match.group(1).split(',') if param_match else []
    params = [p.strip() for p in params]
    
    return PlanInfo(
        function_name=func_name,
        parameters=params,
        description=plan
    )

def generate_code_node(state: Dict[str, Any]) -> DriverState:
    """
    Generate initial code based on the selected plan.
    
    Args:
        state (Dict[str, Any]): Current state of the Driver Agent
    
    Returns:
        DriverState: Updated state with generated code
    """
    try:
        current_state = DriverState(**state)
        
        # If no plan is selected, return the current state
        if not current_state.selected_plan:
            logger.warning("No selected plan found for code generation")
            return current_state

        # Analyze the plan
        plan_info = analyze_plan(current_state.selected_plan)
        
        # Generate function signature
        params_str = ', '.join(plan_info.parameters) if plan_info.parameters else ''
        
        # Generate docstring
        docstring = f'"""\n    {plan_info.description}\n    \n'
        if plan_info.parameters:
            docstring += '    Args:\n'
            for param in plan_info.parameters:
                docstring += f'        {param}: Description of {param}\n'
        docstring += '    \n    Returns:\n        Any: Description of return value\n    """'
        
        # Generate function implementation
        generated_code = [
            f"def {plan_info.function_name}({params_str}):",
            f"    {docstring}",
            "    # TODO: Implement function logic",
            "    pass"
        ]
        
        code = '\n'.join(generated_code)
        logger.info(f"Code generated for plan: {current_state.selected_plan}")
        
        return DriverState(
            **current_state.dict(),
            generated_code=code,
            next="static_analysis"
        )
    
    except Exception as e:
        logger.error(f"Error in code generation: {e}")
        return DriverState(
            **state,
            metadata={'error': str(e)}
        )

def static_analysis_node(state: Dict[str, Any]) -> DriverState:
    """
    Perform static analysis on the generated code.
    
    Args:
        state (Dict[str, Any]): Current state of the Driver Agent
    
    Returns:
        DriverState: Updated state with analysis results
    """
    try:
        current_state = DriverState(**state)
        
        # If no code is generated, return the current state
        if not current_state.generated_code:
            logger.warning("No code to analyze")
            return current_state
        
        syntax_errors = []
        style_warnings = []
        
        # Check syntax using ast
        try:
            ast.parse(current_state.generated_code)
        except SyntaxError as e:
            syntax_errors.append({
                'line': e.lineno,
                'offset': e.offset,
                'message': str(e)
            })
        
        # Basic style checks
        lines = current_state.generated_code.split('\n')
        for i, line in enumerate(lines, 1):
            # Check line length
            if len(line) > 100:
                style_warnings.append({
                    'line': i,
                    'message': 'Line too long (>100 characters)'
                })
            
            # Check indentation
            if line.strip() and not line.startswith((' ', '\t')) and i > 1:
                if lines[i-2].endswith(':'):
                    style_warnings.append({
                        'line': i,
                        'message': 'Expected indented block'
                    })
        
        # Calculate complexity score (simple version)
        complexity_score = 1.0
        if current_state.generated_code:
            # Increase score for each control structure
            complexity_score += current_state.generated_code.count('if ')
            complexity_score += current_state.generated_code.count('for ')
            complexity_score += current_state.generated_code.count('while ')
            complexity_score += current_state.generated_code.count('try')
        
        analysis_results = StaticAnalysisResult(
            syntax_errors=syntax_errors,
            style_warnings=style_warnings,
            complexity_score=complexity_score
        )
        
        test_result = TestResult(
            type='static_analysis',
            results=analysis_results.dict()
        )
        
        updated_test_results = current_state.test_results + [test_result]
        
        logger.info("Static analysis completed")
        return DriverState(
            **current_state.dict(),
            test_results=updated_test_results,
            next="test_code"
        )
    
    except Exception as e:
        logger.error(f"Error in static analysis: {e}")
        return DriverState(
            **state,
            metadata={'error': str(e)}
        )

def test_code_node(state: Dict[str, Any]) -> DriverState:
    """
    Run tests on the generated code.
    
    Args:
        state (Dict[str, Any]): Current state of the Driver Agent
    
    Returns:
        DriverState: Updated state with test results
    """
    try:
        current_state = DriverState(**state)
        
        # If no code is generated, return the current state
        if not current_state.generated_code:
            logger.warning("No code to test")
            return current_state
        
        # Run unit tests (mock implementation)
        unit_test_results = {
            'passed_tests': 0,
            'failed_tests': 0,
            'test_output': []
        }
        
        test_result = TestResult(
            type='unit_tests',
            results=unit_test_results
        )
        
        updated_test_results = current_state.test_results + [test_result]
        
        logger.info("Code testing completed")
        return DriverState(
            **current_state.dict(),
            test_results=updated_test_results,
            next="fix_code" if unit_test_results['failed_tests'] > 0 else None
        )
    
    except Exception as e:
        logger.error(f"Error in code testing: {e}")
        return DriverState(
            **state,
            metadata={'error': str(e)}
        )

def fix_code_node(state: Dict[str, Any]) -> DriverState:
    """
    Refine code based on test results and analysis.
    
    Args:
        state (Dict[str, Any]): Current state of the Driver Agent
    
    Returns:
        DriverState: Updated state with refined code
    """
    try:
        current_state = DriverState(**state)
        
        # If no test results, return current state
        if not current_state.test_results:
            logger.warning("No test results to analyze for refinement")
            return DriverState(**current_state.dict(), refined_code=current_state.generated_code)
        
        # Get the latest analysis results
        analysis_results = next(
            (result.results for result in reversed(current_state.test_results) 
             if result.type == 'static_analysis'),
            None
        )
        
        # Get the latest test results
        test_results = next(
            (result.results for result in reversed(current_state.test_results)
             if result.type == 'unit_tests'),
            None
        )
        
        # If no analysis or test results, return current state
        if not analysis_results and not test_results:
            return DriverState(**current_state.dict(), refined_code=current_state.generated_code)
        
        # Start with the original code
        code_lines = current_state.generated_code.split('\n')
        refinements_needed = []
        
        # Handle syntax errors first
        if analysis_results and analysis_results.get('syntax_errors'):
            for error in analysis_results['syntax_errors']:
                refinements_needed.append(f"Fix syntax error on line {error['line']}: {error['message']}")
        
        # Handle style warnings
        if analysis_results and analysis_results.get('style_warnings'):
            for warning in analysis_results['style_warnings']:
                refinements_needed.append(f"Fix style warning on line {warning['line']}: {warning['message']}")
        
        # If no refinements needed, return current state
        if not refinements_needed:
            return DriverState(**current_state.dict(), refined_code=current_state.generated_code)
        
        # Add a comment about refinements
        refined_code_lines = code_lines + [
            "# Refinements:",
            *[f"# {ref}" for ref in refinements_needed]
        ]
        
        refined_code = '\n'.join(refined_code_lines)
        
        logger.info("Code refinement completed")
        return DriverState(
            **current_state.dict(),
            refined_code=refined_code,
            next="test_code"
        )
    
    except Exception as e:
        logger.error(f"Error in code refinement: {e}")
        return DriverState(
            **state,
            metadata={'error': str(e)}
        )
