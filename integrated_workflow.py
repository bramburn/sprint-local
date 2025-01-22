from typing import Dict, Any, Optional, List
import asyncio
from memory import NavigatorMemorySaver
import config
import os
from backlog_generator import BacklogGenerator
from pydantic import BaseModel
from langchain.tools import ShellTool
from langchain.llms import BaseLLM
from analyzers.typescript_analyzer import TypeScriptAnalyzer
import subprocess
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Debugging output
print("integrated_workflow.py loaded")

class IntegratedWorkflow:
    """
    Orchestrates the workflow between Navigator and Driver agents to process
    problem descriptions and generate solutions seamlessly.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize the integrated workflow.
        
        Args:
            storage_path (Optional[str]): Path for persistent storage.
                                        Defaults to None (uses config.STORAGE_PATH).
        """
        self.storage_path = storage_path or os.path.join(config.STORAGE_PATH, "navigator")
        self.memory_saver = NavigatorMemorySaver(self.storage_path)
        
    async def orchestrate_workflow(
        self,
        problem_description: str,
        thread_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Orchestrate the complete workflow from problem description to solution.
        
        Args:
            problem_description (str): The user's problem description.
            thread_id (Optional[str]): Unique identifier for the workflow thread.
                                     Defaults to None.
        
        Returns:
            Dict[str, Any]: The complete solution including:
                           - refined_problem: The refined problem description
                           - selected_plan: The selected implementation plan
                           - generated_code: The final code solution
                           - test_results: Results of code testing
        """
        # Create workflow configuration
        workflow_config = {
            "thread_id": thread_id or "default",
            "problem_description": problem_description
        }
        
        try:
            # Local import to avoid circular dependency
            from navigator_graph import create_navigator_graph
            navigator_graph = create_navigator_graph()
            
            # Run Navigator to get implementation plan
            navigator_result = await navigator_graph.ainvoke({
                "problem_description": problem_description,
                "thread_id": workflow_config["thread_id"]
            })
            
            # Convert navigator_result to dict if it's a Pydantic model
            if isinstance(navigator_result, BaseModel):
                navigator_result = navigator_result.dict()
            elif hasattr(navigator_result, 'model_dump'):
                navigator_result = navigator_result.model_dump()
            elif hasattr(navigator_result, '__dict__'):
                navigator_result = dict(navigator_result)
            
            required_keys = ["selected_plan"]
            if not all(key in navigator_result for key in required_keys):
                raise ValueError("Navigator failed to generate a valid plan")
            
            # Local import to avoid circular dependency
            from driver_graph import create_driver_graph
            driver_graph = create_driver_graph()
            
            # Run Driver to implement the solution
            driver_result = await driver_graph.ainvoke({
                "implementation_plan": navigator_result["selected_plan"],
                "thread_id": workflow_config["thread_id"]
            })
            
            # Convert driver_result to dict if it's a Pydantic model
            if isinstance(driver_result, BaseModel):
                driver_result = driver_result.dict()
            elif hasattr(driver_result, 'model_dump'):
                driver_result = driver_result.model_dump()
            elif hasattr(driver_result, '__dict__'):
                driver_result = dict(driver_result)
            
            required_keys = ["generated_code"]
            if not all(key in driver_result for key in required_keys):
                raise ValueError("Driver failed to generate code solution")
            
            # Combine results
            solution = {
                "refined_problem": navigator_result.get("refined_problem", ""),
                "selected_plan": navigator_result.get("selected_plan", ""),
                "generated_code": driver_result.get("generated_code", ""),
                "test_results": driver_result.get("test_results", {}),
                "thread_id": workflow_config["thread_id"],
                "status": "success"
            }
            
            return solution
            
        except Exception as e:
            # Load previous checkpoint if available
            checkpoint = await self.memory_saver.get(workflow_config)
            
            error_response = {
                "error": str(e),
                "last_checkpoint": checkpoint,
                "status": "failed"
            }
            
            return error_response
    
    async def get_workflow_state(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve the state of a specific workflow thread.
        
        Args:
            thread_id (str): The unique identifier of the workflow thread.
        
        Returns:
            Optional[Dict[str, Any]]: The workflow state if found, None otherwise.
        """
        return await self.memory_saver.get({"thread_id": thread_id})
    
    async def clear_workflow_state(self, thread_id: Optional[str] = None) -> None:
        """
        Clear the state of a specific workflow thread or all threads.
        
        Args:
            thread_id (Optional[str]): The thread ID to clear. If None, clears all threads.
        """
        if thread_id:
            await self.memory_saver.delete({"thread_id": thread_id})
        else:
            await self.memory_saver.clear()
    
    async def generate_backlog(
        self, 
        prompt: str, 
        thread_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a detailed backlog from a given prompt.
        
        Args:
            prompt (str): The input prompt describing the feature or task.
            thread_id (Optional[str]): Unique identifier for the workflow thread.
        
        Returns:
            Dict[str, Any]: A dictionary containing the generated backlog details.
        """
        workflow_config = {
            "thread_id": thread_id or "default",
            "prompt": prompt
        }
        
        try:
            backlog_generator = BacklogGenerator()
            backlog_text = backlog_generator.generate_backlog(prompt)
            
            return {
                "thread_id": workflow_config["thread_id"],
                "backlog_text": backlog_text,
                "status": "success"
            }
        except Exception as e:
            return {
                "thread_id": workflow_config["thread_id"],
                "error": str(e),
                "status": "error"
            }

def execute_test_command(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executes the test command and updates the workflow state.

    Args:
        state (dict): The current workflow state.

    Returns:
        dict: The updated workflow state.
    """
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    # Extract test command from state
    test_cmd = state.get('test_cmd')
    
    if not test_cmd:
        logger.warning("No test command provided in the workflow state.")
        state['test_output'] = ""
        state['test_error'] = "No test command specified"
        return state

    try:
        # Use subprocess for more robust command execution
        result = subprocess.run(
            test_cmd, 
            shell=True, 
            capture_output=True, 
            text=True, 
            check=False  # Don't raise exception on non-zero exit code
        )

        # Capture stdout and stderr
        state['test_output'] = result.stdout
        state['test_error'] = result.stderr
        state['test_exit_code'] = result.returncode

        # Log the results
        if result.returncode == 0:
            logger.info(f"Test command executed successfully: {test_cmd}")
            logger.info(f"Test Output: {result.stdout}")
        else:
            logger.error(f"Test command failed with exit code {result.returncode}")
            logger.error(f"Test Error: {result.stderr}")

    except Exception as e:
        # Catch any unexpected errors during command execution
        error_msg = f"Error executing test command: {str(e)}"
        logger.error(error_msg)
        state['test_error'] = error_msg
        state['test_output'] = ""
        state['test_exit_code'] = -1

    return state

# Convenience function for synchronous usage
def run_workflow(
    problem_description: str,
    thread_id: Optional[str] = None,
    storage_path: Optional[str] = None,
    workflow_type: str = "solution"
) -> Dict[str, Any]:
    """
    Synchronous wrapper for running the integrated workflow.
    
    Args:
        problem_description (str): The user's problem description.
        thread_id (Optional[str]): Unique identifier for the workflow thread.
        storage_path (Optional[str]): Path for persistent storage.
        workflow_type (str): Type of workflow to run - 'solution' or 'backlog'.
    
    Returns:
        Dict[str, Any]: The complete solution or error response.
    """
    print(f"Running workflow for: {problem_description}")  # Debug: Log workflow start
    workflow = IntegratedWorkflow(storage_path)
    
    if workflow_type == "solution":
        return asyncio.run(workflow.orchestrate_workflow(problem_description, thread_id))
    elif workflow_type == "backlog":
        return asyncio.run(workflow.generate_backlog(problem_description, thread_id))
    else:
        return {
            "error": f"Invalid workflow type: {workflow_type}",
            "status": "error"
        }

def run_workflow_with_test_cmd(
    test_cmd: str,
    repo: str,
    thread_id: Optional[str] = None,
    storage_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run the workflow with a specific test command and repository.

    Args:
        test_cmd (str): The command to run tests.
        repo (str): The repository directory.
        thread_id (Optional[str]): Unique identifier for the workflow thread.
        storage_path (Optional[str]): Path for persistent storage.

    Returns:
        Dict[str, Any]: The workflow results.
    """
    # Create workflow configuration
    workflow_config = {
        "thread_id": thread_id or "default",
        "test_cmd": test_cmd,
        "repo": repo
    }

    workflow = IntegratedWorkflow(storage_path)

    try:
        # Change current working directory to the repository
        original_cwd = os.getcwd()
        os.chdir(repo)

        # Run the test command
        test_state = execute_test_command(workflow_config)

        # Restore original working directory
        os.chdir(original_cwd)

        # Prepare results
        results = {
            "test_cmd": test_cmd,
            "test_output": test_state.get('test_output', ''),
            "test_error": test_state.get('test_error', ''),
            "test_exit_code": test_state.get('test_exit_code', -1),
            "thread_id": workflow_config["thread_id"],
            "status": "success" if test_state.get('test_exit_code', -1) == 0 else "failed"
        }

        return results

    except Exception as e:
        print(f"Error in run_workflow_with_test_cmd: {str(e)}")  # Debug: Log error
        return {
            "error": str(e),
            "status": "failed",
            "thread_id": workflow_config["thread_id"]
        }

def verify_fixes(
    file_paths: List[str], 
    llm: BaseLLM, 
    max_attempts: int = 3
) -> bool:
    """
    Validates applied fixes and iteratively resolves remaining errors.

    Args:
        file_paths (List[str]): List of file paths to validate.
        llm (BaseLLM): The LLM instance for error validation.
        max_attempts (int, optional): Maximum number of fix attempts. Defaults to 3.

    Returns:
        bool: True if no errors are found, False otherwise.
    """
    try:
        logging.info(f"Verifying fixes for files: {file_paths}")
        
        # Initial verification
        response = llm.predict(f"Check for any errors in the following files: {', '.join(file_paths)}")
        logging.info(f"Initial LLM verification response: {response}")
        
        # If no errors are found initially
        if "no errors found" in response.lower():
            return True
        
        # If errors are found, attempt to re-apply fixes
        for attempt in range(1, max_attempts + 1):
            logging.info(f"Fix attempt {attempt}/{max_attempts}")
            
            # Apply fixes
            analyzer = TypeScriptAnalyzer()
            analyzer.generate_and_apply_fixes(file_paths)
            
            # Re-verify
            response = llm.predict(f"Check for any errors in the following files after applying fixes: {', '.join(file_paths)}")
            logging.info(f"LLM verification response (Attempt {attempt}): {response}")
            
            if "no errors found" in response.lower():
                logging.info(f"Fixes successful on attempt {attempt}")
                return True
        
        logging.warning(f"Maximum fix attempts ({max_attempts}) reached without resolving errors")
        return False
    
    except Exception as e:
        logging.error(f"Error during fix verification: {e}")
        return False

def rerun_tests(test_command: str) -> str:
    """
    Re-runs the test command and captures the output.

    Args:
        test_command: The test command to execute.

    Returns:
        The output of the test command.
    """
    shell_tool = ShellTool()
    try:
        output = shell_tool.run(test_command)
        return output
    except Exception as e:
        logging.error(f"Error executing test command: {e}")
        return str(e)

def analyze_test_output(test_output: str) -> bool:
    """
    Analyzes the test output to determine if the workflow should continue or terminate.

    Args:
        test_output: The output of the test command.

    Returns:
        True if the workflow should continue (errors present), False otherwise.
    """
    # Check for common error indicators
    error_indicators = ['error', 'fail', 'exception', 'traceback']
    
    # Convert test output to lowercase for case-insensitive matching
    test_output_lower = test_output.lower()
    
    # Check if any error indicators are present
    for indicator in error_indicators:
        if indicator in test_output_lower:
            return True
    
    return False

def log_final_outcome(errors_resolved: bool) -> None:
    """
    Logs the final outcome of the workflow execution.

    Args:
        errors_resolved: True if the errors were resolved, False otherwise.
    """
    if errors_resolved:
        logging.info("Workflow completed successfully. All errors were resolved.")
    else:
        logging.warning("Workflow completed with errors. Not all errors were resolved.")

def run_workflow_with_analysis(
    test_command: str, 
    file_paths: List[str], 
    llm: BaseLLM
) -> None:
    """
    Runs the workflow with test command analysis.

    Args:
        test_command: The test command to execute.
        file_paths: A list of file paths.
        llm: The LLM to use.
    """
    # Re-run tests
    test_output = rerun_tests(test_command)
    
    # Analyze test output
    continue_workflow = analyze_test_output(test_output)
    
    if continue_workflow:
        # Logic to continue the workflow
        logging.info("Continuing the workflow due to detected errors.")
        # Add your specific workflow continuation logic here
    else:
        log_final_outcome(True)
        logging.info("Workflow finished successfully.")

import subprocess
import logging
from typing import Dict, Any
from langchain_core.language_models import BaseLanguageModel
from navigator_state import NavigatorState
from driver_state import DriverState

logger = logging.getLogger(__name__)

class TestExecutionNode:
    def __init__(self, llm: BaseLanguageModel):
        self.llm = llm

    def __call__(self, state: NavigatorState) -> Dict[str, Any]:
        """
        Execute the test command and capture the output.
        
        Args:
            state (NavigatorState): Current state of the navigator
        
        Returns:
            Dict[str, Any]: Updated state with test execution results
        """
        try:
            test_cmd = state.memory.get('test_cmd', 'pytest')
            repo_path = state.memory.get('repo_path', '.')
            
            result = subprocess.run(
                test_cmd.split(), 
                cwd=repo_path, 
                capture_output=True, 
                text=True
            )
            
            state.memory['test_output'] = result.stdout
            state.memory['test_error'] = result.stderr
            state.memory['test_status'] = 'passed' if result.returncode == 0 else 'failed'
            
            return state
        except Exception as e:
            logger.error(f"Test execution failed: {e}")
            state.memory['test_status'] = 'error'
            state.memory['test_error'] = str(e)
            return state

class ErrorAnalysisNode:
    def __init__(self, llm: BaseLanguageModel):
        self.llm = llm

    def __call__(self, state: NavigatorState) -> Dict[str, Any]:
        """
        Analyze test errors and determine next steps.
        
        Args:
            state (NavigatorState): Current state of the navigator
        
        Returns:
            Dict[str, Any]: Updated state with error analysis results
        """
        try:
            test_output = state.memory.get('test_output', '')
            test_error = state.memory.get('test_error', '')
            
            # Use LLM to analyze errors
            error_analysis_prompt = f"""
            Analyze the following test output and error:
            
            Test Output: {test_output}
            Test Error: {test_error}
            
            Provide a detailed breakdown of the errors and suggest potential fixes.
            """
            
            error_analysis = self.llm.invoke(error_analysis_prompt)
            
            state.memory['error_analysis'] = error_analysis.content
            state.memory['error_status'] = 'analyze' if test_error else 'terminate'
            
            return state
        except Exception as e:
            logger.error(f"Error analysis failed: {e}")
            state.memory['error_status'] = 'terminate'
            return state

class TestFixNode:
    def __call__(self, state: DriverState) -> Dict[str, Any]:
        """
        Attempt to fix the code based on test errors.
        
        Args:
            state (DriverState): Current state of the driver
        
        Returns:
            Dict[str, Any]: Updated state with test fix results
        """
        try:
            error_analysis = state.memory.get('error_analysis', '')
            
            # Generate potential fixes
            fix_prompt = f"""
            Based on the following error analysis, generate a code fix:
            
            Error Analysis: {error_analysis}
            
            Provide a concise, precise code fix that addresses the identified issues.
            """
            
            # Simulating code fix generation (replace with actual LLM call)
            code_fix = "# Placeholder for generated code fix"
            
            state.memory['code_fix'] = code_fix
            state.memory['fix_status'] = 'generated'
            
            return state
        except Exception as e:
            logger.error(f"Test fix generation failed: {e}")
            state.memory['fix_status'] = 'error'
            return state

class ValidationNode:
    def __call__(self, state: DriverState) -> Dict[str, Any]:
        """
        Validate the generated code fix by running tests.
        
        Args:
            state (DriverState): Current state of the driver
        
        Returns:
            Dict[str, Any]: Updated state with validation results
        """
        try:
            code_fix = state.memory.get('code_fix', '')
            
            # Apply code fix
            # This is a placeholder - in a real scenario, you'd apply the fix to the actual code
            
            # Run tests again
            result = subprocess.run(
                ['pytest'], 
                capture_output=True, 
                text=True
            )
            
            state.memory['test_results'] = {
                'status': 'passed' if result.returncode == 0 else 'failed',
                'output': result.stdout,
                'error': result.stderr
            }
            
            return state
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            state.memory['test_results'] = {
                'status': 'error',
                'error': str(e)
            }
            return state

def some_function():
    from navigator_graph import create_navigator_graph  # Local import to avoid circular dependency
    # ... existing code ...