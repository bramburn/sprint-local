from typing import Dict, Any, Optional
import asyncio
from navigator_graph import create_navigator_graph
from driver_graph import create_driver_graph
from memory import NavigatorMemorySaver
import config
import os
from backlog_generator import BacklogGenerator

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
            # Create Navigator graph
            navigator_graph = create_navigator_graph(self.memory_saver)
            
            # Run Navigator to get implementation plan
            navigator_result = await navigator_graph.ainvoke({
                "problem_description": problem_description,
                "thread_id": workflow_config["thread_id"]
            })
            
            if not navigator_result.get("selected_plan"):
                raise ValueError("Navigator failed to generate a valid plan")
            
            # Create Driver graph
            driver_graph = create_driver_graph()
            
            # Run Driver to implement the solution
            driver_result = await driver_graph.ainvoke({
                "implementation_plan": navigator_result["selected_plan"],
                "thread_id": workflow_config["thread_id"]
            })
            
            if not driver_result.get("generated_code"):
                raise ValueError("Driver failed to generate code solution")
            
            # Combine results
            solution = {
                "refined_problem": navigator_result.get("refined_problem"),
                "selected_plan": navigator_result["selected_plan"],
                "generated_code": driver_result["generated_code"],
                "test_results": driver_result.get("test_results", {})
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