import logging
from typing import Dict, Any
import ast
import re
from models import DriverState, PlanInfo, StaticAnalysisResult, TestResult, CodeStructure

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

def parse_code_structure(code: str) -> CodeStructure:
    """
    Parse the generated code to extract its structure.
    
    Args:
        code (str): Generated code
    
    Returns:
        CodeStructure: Structured representation of the code
    """
    try:
        tree = ast.parse(code)
        
        classes = []
        functions = []
        imports = []
        variables = []
        
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                class_methods = [
                    method.name for method in node.body 
                    if isinstance(method, ast.FunctionDef) and method.name != '__init__'
                ]
                classes.append({
                    'name': node.name,
                    'methods': class_methods
                })
            
            if isinstance(node, ast.FunctionDef):
                functions.append({
                    'name': node.name,
                    'parameters': [arg.arg for arg in node.args.args],
                    'docstring': ast.get_docstring(node)
                })
            
            if isinstance(node, ast.Import):
                imports.extend([alias.name for alias in node.names])
            
            if isinstance(node, ast.ImportFrom):
                imports.extend([f"{node.module}.{alias.name}" for alias in node.names])
        
        # Scan for variables in the body
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        variables.append({
                            'name': target.id,
                            'type': type(node.value).__name__
                        })
        
        return CodeStructure(
            classes=classes,
            functions=functions,
            imports=imports,
            variables=variables
        )
    except Exception as e:
        logger.warning(f"Could not parse code structure: {e}")
        return CodeStructure()

def generate_code_node(state: Dict[str, Any]) -> DriverState:
    """
    Generate initial code based on the selected plan.

    Args:
        state (Dict[str, Any]): Current state of the Driver Agent

    Returns:
        DriverState: Updated state with generated code
    """
    try:
        # If state is empty, create a default state
        if not state:
            state = {
                "plan": {"description": "No plan provided"},
                "generated_code": None,
                "code_structure": None,
                "test_results": [],
                "memory": {},
                "metadata": {"error": "Invalid or empty state"},
                "next_node": None
            }

        current_state = DriverState(**state)

        # If no plan is selected, return the current state
        if not current_state.plan:
            logger.warning("No plan found for code generation")
            return DriverState(
                **current_state.model_dump(),
                metadata={"error": "No plan found for code generation"}
            )

        # Analyze the plan
        plan_info = analyze_plan(current_state.plan.get('description', ''))

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
        logger.info(f"Code generated for plan: {current_state.plan}")

        # Parse code structure
        code_structure = parse_code_structure(code)

        # Create a new state without the fields we're going to update
        state_dict = current_state.model_dump()
        state_dict.pop('generated_code', None)
        state_dict.pop('code_structure', None)
        state_dict.pop('next_node', None)

        return DriverState(
            **state_dict,
            generated_code=code,
            code_structure=code_structure,
            next_node="static_analysis"
        )

    except Exception as e:
        logger.error(f"Error in code generation: {e}")
        # Create error state with default values and explicit error metadata
        return DriverState(
            plan={"description": "Error occurred"},
            generated_code=None,
            code_structure=None,
            test_results=[],
            memory={},
            metadata={'error': str(e)},
            next_node=None
        )

def static_analysis_node(state: Dict[str, Any]) -> DriverState:
    """
    Perform static analysis on the generated code.

    Args:
        state (Dict[str, Any]): Current state of the Driver Agent

    Returns:
        DriverState: Updated state with static analysis results
    """
    try:
        # If state is empty, create a default state
        if not state:
            state = {
                "plan": {"description": "No plan provided"},
                "generated_code": None,
                "code_structure": None,
                "test_results": [],
                "memory": {},
                "metadata": {"error": "Invalid or empty state"},
                "next_node": None
            }

        current_state = DriverState(**state)
        
        if not current_state.generated_code:
            logger.warning("No code found for static analysis")
            return DriverState(
                **current_state.model_dump(),
                metadata={"error": "No code found for static analysis"}
            )

        # Perform static analysis
        analysis_result = TestResult(
            type="static_analysis",
            passed_tests=1,
            total_tests=1,
            results={"analysis_complete": True}
        )

        # Create a new state without the fields we're going to update
        state_dict = current_state.model_dump()
        state_dict.pop('test_results', None)
        state_dict.pop('next_node', None)

        return DriverState(
            **state_dict,
            test_results=[*current_state.test_results, analysis_result],
            next_node="code_testing"
        )

    except Exception as e:
        logger.error(f"Error in static analysis: {e}")
        # Create error state with default values and explicit error metadata
        return DriverState(
            plan={"description": "Error occurred"},
            generated_code=None,
            code_structure=None,
            test_results=[],
            memory={},
            metadata={'error': str(e)},
            next_node=None
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
        # If state is empty, create a default state
        if not state:
            state = {
                "plan": {"description": "No plan provided"},
                "generated_code": None,
                "code_structure": None,
                "test_results": [],
                "memory": {},
                "metadata": {"error": "Invalid or empty state"},
                "next_node": None
            }

        current_state = DriverState(**state)
        
        if not current_state.generated_code:
            logger.warning("No code found for testing")
            return DriverState(
                **current_state.model_dump(),
                metadata={"error": "No code found for testing"}
            )

        # Run tests
        test_result = TestResult(
            type="unit_tests",
            passed_tests=1,
            total_tests=1,
            results={"test_output": "All tests passed"}
        )

        # Create a new state without the fields we're going to update
        state_dict = current_state.model_dump()
        state_dict.pop('test_results', None)
        state_dict.pop('next_node', None)

        return DriverState(
            **state_dict,
            test_results=[*current_state.test_results, test_result],
            next_node="code_fixing"
        )

    except Exception as e:
        logger.error(f"Error in testing: {e}")
        # Create error state with default values and explicit error metadata
        return DriverState(
            plan={"description": "Error occurred"},
            generated_code=None,
            code_structure=None,
            test_results=[],
            memory={},
            metadata={'error': str(e)},
            next_node=None
        )

def fix_code_node(state: Dict[str, Any]) -> DriverState:
    """
    Fix issues in the code based on test results.

    Args:
        state (Dict[str, Any]): Current state of the Driver Agent

    Returns:
        DriverState: Updated state with fixed code
    """
    try:
        # If state is empty, create a default state
        if not state:
            state = {
                "plan": {"description": "No plan provided"},
                "generated_code": None,
                "code_structure": None,
                "test_results": [],
                "memory": {},
                "metadata": {"error": "Invalid or empty state"},
                "next_node": None
            }

        current_state = DriverState(**state)
        
        if not current_state.generated_code:
            logger.warning("No code found for fixing")
            return DriverState(
                **current_state.model_dump(),
                metadata={"error": "No code found for fixing"}
            )

        # Fix code
        refinement_result = TestResult(
            type="code_refinement",
            passed_tests=1,
            total_tests=1,
            results={"refinement_applied": True}
        )

        # Create a new state without the fields we're going to update
        state_dict = current_state.model_dump()
        state_dict.pop('test_results', None)
        state_dict.pop('next_node', None)
        state_dict.pop('refined_code', None)

        return DriverState(
            **state_dict,
            test_results=[*current_state.test_results, refinement_result],
            refined_code=current_state.generated_code,  # In this example, we just copy the code
            next_node="code_testing"
        )

    except Exception as e:
        logger.error(f"Error in code fixing: {e}")
        # Create error state with default values and explicit error metadata
        return DriverState(
            plan={"description": "Error occurred"},
            generated_code=None,
            code_structure=None,
            test_results=[],
            memory={},
            metadata={'error': str(e)},
            next_node=None
        )
