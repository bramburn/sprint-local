import click
from click.testing import CliRunner
from cli import cli

def test_cli():
    runner = CliRunner()
    result = runner.invoke(cli, ['--test-cmd', 'pytest', '--repo', '/path/to/repo'])
    assert result.exit_code == 0
    assert 'Running command: pytest in repository: /path/to/repo' in result.output
