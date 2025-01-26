import click
import json
from typing import Optional
import os
import config
import asyncio
from .backlog_generator import BacklogGenerator
import argparse
import sys
from pathlib import Path
from .documentation import add_docs as add_documentation

# Debugging output
print("cli_interface.py loaded")

def format_output(data: dict, format_json: bool = False) -> str:
    """Format the output data either as JSON or human-readable text."""
    if format_json:
        return json.dumps(data, indent=2)
    
    if "error" in data:
        return f"Error: {data['error']}\nLast checkpoint: {data.get('last_checkpoint')}"
    
    output = []
    output.append("✨ Solution Generated Successfully ✨\n")
    
    if data.get("refined_problem"):
        output.append("📝 Refined Problem:")
        output.append(f"{data['refined_problem']}\n")
    
    if data.get("selected_plan"):
        output.append("🎯 Implementation Plan:")
        output.append(f"{data['selected_plan']}\n")
    
    if data.get("generated_code"):
        output.append("💻 Generated Code:")
        output.append(f"{data['generated_code']}\n")
    
    if data.get("test_results"):
        output.append("🧪 Test Results:")
        output.append(json.dumps(data["test_results"], indent=2))
    
    return "\n".join(output)

@click.group()
def cli():
    """Sprint CLI - A tool for automated software development using AI agents."""
    pass

@cli.command()
@click.argument('problem_description', required=True)
@click.option('--thread-id', '-t', help='Unique identifier for the workflow thread')
@click.option('--json', '-j', is_flag=True, help='Output results in JSON format')
@click.option('--storage-path', help='Custom storage path for workflow state')
def solve(
    problem_description: str,
    thread_id: Optional[str] = None,
    json: bool = False,
    storage_path: Optional[str] = None
):
    """Generate a solution for the given problem description."""
    print(f"Solving problem: {problem_description}")  # Debug: Log problem description
    try:
        # Local import to avoid circular dependency
        from .integrated_workflow import run_workflow
        result = run_workflow(
            problem_description=problem_description,
            thread_id=thread_id,
            storage_path=storage_path or os.path.join(config.STORAGE_PATH, "navigator")
        )
        print(f"Result: {result}")  # Debug: Log result
        click.echo(format_output(result, json))
    except Exception as e:
        print(f"Error in solve: {str(e)}")  # Debug: Log error
        click.echo(f"Error: {str(e)}", err=True)
        exit(1)

@cli.command()
@click.argument('thread_id', required=True)
@click.option('--json', '-j', is_flag=True, help='Output state in JSON format')
def state(thread_id: str, json: bool = False):
    """Retrieve the state of a specific workflow thread."""
    try:
        # Local import to avoid circular dependency
        from .integrated_workflow import IntegratedWorkflow
        workflow = IntegratedWorkflow()
        state = asyncio.run(workflow.get_workflow_state(thread_id))
        if state:
            click.echo(format_output(state, json))
        else:
            click.echo(f"No state found for thread ID: {thread_id}")
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        exit(1)

@cli.command()
@click.argument('thread_id', required=False)
def clear(thread_id: Optional[str] = None):
    """Clear workflow state for a specific thread or all threads."""
    try:
        # Local import to avoid circular dependency
        from .integrated_workflow import IntegratedWorkflow
        workflow = IntegratedWorkflow()
        asyncio.run(workflow.clear_workflow_state(thread_id))
        if thread_id:
            click.echo(f"Cleared state for thread ID: {thread_id}")
        else:
            click.echo("Cleared all workflow states")
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        exit(1)

@cli.command()
def version():
    """Display the current version of the Sprint CLI."""
    click.echo("Sprint CLI v0.1.0")

@cli.command()
@click.argument('prompt', required=True)
@click.option('--output', '-o', type=click.Path(), help='Path to save the generated backlog')
def generate_backlog(prompt: str, output: Optional[str] = None):
    """Generate a detailed backlog from a given prompt."""
    generator = BacklogGenerator()
    backlog = generator.generate_backlog(prompt)
    
    if output:
        with open(output, 'w') as f:
            f.write(backlog)
        click.echo(f"Backlog saved to {output}")
    else:
        click.echo(backlog)

@click.command()
@click.option('--prompt', '-p', required=True, help='The prompt to send to the LLM')

def langchain_command(prompt: str):
    """
    Execute the Langchain LLM interaction.
    """
    from .langchain_file import LangchainFile
    try:
        langchain_file = LangchainFile(     
           
        )

        

        response = langchain_file.run(prompt)
        click.echo(response)
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        exit(1)

cli.add_command(langchain_command, name='langchain')

def setup_parser():
    """
    Set up the argument parser for the CLI.
    """
    parser = argparse.ArgumentParser(
        description='CLI interface for managing vector stores'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Add documentation command
    docs_parser = subparsers.add_parser(
        'add-docs',
        help='Add documentation files to the vector store'
    )
    docs_parser.add_argument(
        'file_path',
        type=str,
        help='Path to the documentation file to add'
    )
    docs_parser.add_argument(
        '--name',
        type=str,
        help='Name of the document to add'
    )
    docs_parser.add_argument(
        '--vector-store-path',
        type=str,
        default='vector_store/documentation',
        help='Path to store the vector store (default: vector_store/documentation)'
    )
    
    return parser

def main():
    """
    Main entry point for the CLI.
    """
    parser = setup_parser()
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return 1
    
    try:
        if args.command == 'add-docs':
            # Ensure the vector store directory exists
            vector_store_path = Path(args.vector_store_path)
            vector_store_path.mkdir(parents=True, exist_ok=True)
            
            # Add the documentation to the vector store
            add_documentation(args.file_path, str(vector_store_path), args.name)
            
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        return 1
        
    return 0

if __name__ == '__main__':
    exit(main()) 