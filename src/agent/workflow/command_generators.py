import os
from .schemas import TestFramework, TestCommandGenerationResult

def generate_command(framework: TestFramework, repo_path: str) -> TestCommandGenerationResult:
    """
    Generate appropriate test command for the detected framework.
    
    Args:
        framework: Detected testing framework
        repo_path: Path to the repository
    
    Returns:
        Test command generation result
    """
    command_templates = {
        TestFramework.PYTEST: "poetry run pytest",
        TestFramework.JEST: "npm run test",
        TestFramework.VITEST: "npm run test:vitest",
        TestFramework.NPM: "npm test",
        TestFramework.UNKNOWN: None
    }
    
    command = command_templates.get(framework)
    
    if not command:
        return TestCommandGenerationResult(
            command="",
            framework=framework,
            is_valid=False,
            error_message="Unable to generate test command for unknown framework"
        )
    
    # Validate command by checking if command exists in PATH or project
    try:
        # Add additional validation logic if needed
        is_valid = os.path.exists(os.path.join(repo_path, 'pyproject.toml')) or \
                   os.path.exists(os.path.join(repo_path, 'package.json'))
        
        return TestCommandGenerationResult(
            command=command,
            framework=framework,
            is_valid=is_valid,
            error_message=None if is_valid else "Command validation failed"
        )
    except Exception as e:
        return TestCommandGenerationResult(
            command=command,
            framework=framework,
            is_valid=False,
            error_message=str(e)
        )
