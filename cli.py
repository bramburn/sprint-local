import click
from integrated_workflow import run_workflow_with_test_cmd

@click.command()
@click.option('--test-cmd', required=True, help='The command to run tests in the repo.')
@click.option('--repo', required=True, help='The directory where the files can be found.')
def cli(test_cmd, repo):
    """Run the workflow with the specified test command and repository."""
    click.echo(f'Running command: {test_cmd} in repository: {repo}')
    
    # Call the workflow execution function with the test command and repository
    result = run_workflow_with_test_cmd(test_cmd, repo)
    
    # Print the result
    click.echo(f'Workflow Result: {result}')

if __name__ == '__main__':
    cli()
