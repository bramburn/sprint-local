import os
import unittest
import tempfile
from pathlib import Path

from src.agent.workflow.testing_agent_determine_cli import (
    run_testing_agent,
    list_files_in_directory,
    determine_testing_framework,
    construct_test_command
)
from src.utils.dir_tool import scan_directory

class TestTestingAgent(unittest.TestCase):
    def setUp(self):
        """Create a temporary directory for testing."""
        self.test_dir = tempfile.mkdtemp()

    def create_test_files(self, files):
        """Create test files in the temporary directory."""
        for file_path in files:
            full_path = os.path.join(self.test_dir, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            Path(full_path).touch()

    def test_list_files_in_directory(self):
        """Test listing files in a directory."""
        self.create_test_files([
            'src/test_example.py',
            'tests/test_another.py',
            'README.md'
        ])

        state = {'repo_path': self.test_dir}
        result = list_files_in_directory(state)
        
        self.assertIn('files', result)
        self.assertTrue(len(result['files']) > 0)
        self.assertEqual(len(result['errors']), 0)
        
        # Verify files are found using scan_directory directly
        files = scan_directory(self.test_dir)
        self.assertEqual(set(result['files']), set(files))

    def test_determine_testing_framework_pytest(self):
        """Test detecting pytest framework."""
        self.create_test_files([
            'src/test_example.py',
            'conftest.py',
            'pytest.ini'
        ])

        state = {'files': [
            os.path.join(self.test_dir, 'src/test_example.py'),
            os.path.join(self.test_dir, 'conftest.py'),
            os.path.join(self.test_dir, 'pytest.ini')
        ]}
        result = determine_testing_framework(state)
        
        self.assertEqual(result['testing_framework'], 'pytest')

    def test_determine_testing_framework_jest(self):
        """Test detecting jest framework."""
        self.create_test_files([
            'jest.config.js',
            '__tests__/example.test.js'
        ])

        state = {'files': [
            os.path.join(self.test_dir, 'jest.config.js'),
            os.path.join(self.test_dir, '__tests__/example.test.js')
        ]}
        result = determine_testing_framework(state)
        
        self.assertEqual(result['testing_framework'], 'jest')

    def test_construct_test_command(self):
        """Test constructing test commands for different frameworks."""
        test_cases = [
            ('pytest', 'poetry run pytest'),
            ('jest', 'npm run test'),
            ('vitest', 'vitest --watch=false'),
            ('npm', 'npm run test'),
            ('unknown', 'Unable to determine test command')
        ]

        for framework, expected_command in test_cases:
            state = {'testing_framework': framework}
            result = construct_test_command(state)
            
            self.assertEqual(result['test_command'], expected_command)

    def test_run_testing_agent_with_pytest(self):
        """Test running the testing agent with a pytest project."""
        self.create_test_files([
            'src/test_example.py',
            'conftest.py',
            'pytest.ini'
        ])

        result = run_testing_agent(self.test_dir)
        
        self.assertEqual(result['testing_framework'], 'pytest')
        self.assertEqual(result['test_command'], 'poetry run pytest')
        self.assertEqual(len(result['errors']), 0)

    def test_run_testing_agent_with_unknown_framework(self):
        """Test running the testing agent with an unknown framework."""
        self.create_test_files([
            'README.md',
            'src/main.py'
        ])

        result = run_testing_agent(self.test_dir)
        
        self.assertEqual(result['testing_framework'], 'unknown')
        self.assertEqual(result['test_command'], 'Unable to determine test command')
        self.assertEqual(len(result['errors']), 0)

    def test_invalid_repository_path(self):
        """Test running the testing agent with an invalid repository path."""
        invalid_path = '/path/to/nonexistent/directory'
        
        result = run_testing_agent(invalid_path)
        
        self.assertEqual(result['testing_framework'], 'unknown')
        self.assertEqual(result['test_command'], 'Unable to determine test command')
        self.assertTrue(len(result['errors']) > 0)

if __name__ == '__main__':
    unittest.main()
