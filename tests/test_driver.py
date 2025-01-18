from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

def analyze_plan(plan: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze the plan to extract necessary information.
    
    Args:
        plan (Dict[str, Any]): The selected plan
    
    Returns:
        Dict[str, Any]: Analyzed plan information
    """
    return {
        'function_name': plan.get('function_name', 'default_function'),
        'parameters': plan.get('parameters', []),
        'description': plan.get('description', 'A default function.')
    }

def generate_code_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate initial code based on the selected plan.
    
    Args:
        state (Dict[str, Any]): Current state of the Driver Agent
    
    Returns:
        Dict[str, Any]: Updated state attributes
    """
    try:
        # If no plan is selected, return the current state
        if not state.get('selected_plan'):
            logger.warning("No selected plan found for code generation")
            return state

        # Analyze the plan
        plan_info = analyze_plan(state['selected_plan'])
        
        # Generate function signature
        params_str = ', '.join(plan_info['parameters']) if plan_info['parameters'] else ''
        
        # Generate docstring using triple quotes for multi-line strings
        docstring = f'"""{plan_info["description"]}\n'
        
        if plan_info['parameters']:
            docstring += 'Args:\n'
            for param in plan_info['parameters']:
                docstring += f'    {param}: Description of {param}\n'
        docstring += 'Returns:\n'
        docstring += '    Any: Description of return value\n"""'
        
        # Generate function implementation
        generated_code = [
            f"def {plan_info['function_name']}({params_str}):",
            f"    {docstring}",
            "    # TODO: Implement function logic",
            "    pass"
        ]
        
        code = '\n'.join(generated_code)
        logger.info(f"Code generated for plan: {state['selected_plan']}")
        
        # Update the state with generated code
        return {
            **state,
            'generated_code': code,
            'next': 'static_analysis'
        }
    
    except Exception as e:
        logger.error(f"Error in code generation: {e}")
        return {**state, 'metadata': {'error': str(e)}}