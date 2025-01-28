import asyncio
import logging
from typing import Optional, Dict, Any

from .langchain_graph.agent_graph import NavigatorAgentGraph, load_graph_config
from .schemas.agent_state import AgentState

def setup_logging(log_level: str = 'INFO'):
    """
    Configure logging for the Navigator Agent.
    
    :param log_level: Logging level as a string
    """
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {log_level}')
    
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

async def run_navigator_agent(
    problem_statement: str, 
    context: Optional[Dict[str, Any]] = None,
    config_path: Optional[str] = None
) -> AgentState:
    """
    Run the Navigator Agent workflow for a given problem.
    
    :param problem_statement: Description of the problem to solve
    :param context: Optional additional context for the problem
    :param config_path: Optional path to graph configuration file
    :return: Final agent state after workflow execution
    """
    # Load configuration
    config = load_graph_config(config_path) if config_path else {}
    
    # Setup logging based on configuration
    setup_logging(config.get('logging_level', 'INFO'))
    
    # Create initial state
    initial_state = AgentState(
        problem_statement=problem_statement,
        context=context or {}
    )
    
    # Initialize and run workflow
    navigator_graph = NavigatorAgentGraph()
    
    try:
        final_state = await navigator_graph.run_workflow(initial_state)
        logging.info("Navigator Agent workflow completed successfully.")
        return final_state
    
    except Exception as e:
        logging.error(f"Error in Navigator Agent workflow: {e}")
        raise

def main():
    """
    Main entry point for the Navigator Agent CLI.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Navigator Agent CLI")
    parser.add_argument(
        "problem", 
        type=str, 
        help="Problem statement for the Navigator Agent to solve"
    )
    parser.add_argument(
        "--config", 
        type=str, 
        help="Path to graph configuration file",
        default=None
    )
    
    args = parser.parse_args()
    
    # Run the agent synchronously
    final_state = asyncio.run(
        run_navigator_agent(
            problem_statement=args.problem, 
            config_path=args.config
        )
    )
    
    # Print final state details
    print("Final Agent State:")
    print(final_state.model_dump_json(indent=2))

if __name__ == "__main__":
    main()
