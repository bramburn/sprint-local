import unittest
import os
import tempfile
from unittest.mock import MagicMock, patch
from langchain_openai import OpenAI
from analyzers import TypeScriptAnalyzer
import pytest
from unittest.mock import Mock
from langchain.llms import BaseLLM

class TestTypeScriptAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = TypeScriptAnalyzer()

    def test_analyze_empty_code(self):
        with self.assertRaises(ValueError):
            self.analyzer.analyze_code("")

    def test_analyze_basic_class(self):
        code = """
class TestClass {
    private x: number;
    
    constructor(x: number) {
        this.x = x;
    }
    
    testMethod(y: number): number {
        return this.x + y;
    }
}
"""
        result = self.analyzer.analyze_code(code)
        
        self.assertEqual(len(result.classes), 1)
        test_class = result.classes[0]
        self.assertEqual(test_class['name'], 'TestClass')
        self.assertEqual(len(test_class['methods']), 2)
        
        # Check methods
        method_names = {m['name'] for m in test_class['methods']}
        self.assertEqual(method_names, {'constructor', 'testMethod'})

    def test_analyze_functions(self):
        code = """
function testFunc1(x: number, y: number): number {
    return x + y;
}
"""
        result = self.analyzer.analyze_code(code)
        
        assert len(result.functions) == 1
        assert result.functions[0]['name'] == 'testFunc1'
        assert result.functions[0]['args'] == ['x', 'y']
        assert result.functions[0]['returns'] == 'number'
        assert result.functions[0]['is_async'] == False

    def test_analyze_imports(self):
        code = """
import { Component } from '@angular/core';
import { HttpClient } from '@angular/common/http';
"""
        result = self.analyzer.analyze_code(code)
        
        assert len(result.imports) == 2
        import_names = {imp['module'] for imp in result.imports}
        assert import_names == {'@angular/core', '@angular/common/http'}

    def test_analyze_variables(self):
        code = """
const x: number = 1;
let y: string, z: boolean;
const CONSTANT = "test";
"""
        result = self.analyzer.analyze_code(code)
        
        expected_variables = {'x', 'y', 'z', 'CONSTANT'}
        actual_variables = {v['name'] for v in result.variables}
        self.assertEqual(actual_variables, expected_variables)

    def test_invalid_code(self):
        # Provide syntactically incorrect TypeScript code
        invalid_code = """
class Incomplete {
    // Missing closing brace
"""
        with self.assertRaises(ValueError):
            self.analyzer.analyze_code(invalid_code)

class TestTypeScriptAnalyzerErrorFix(unittest.TestCase):
    def setUp(self):
        self.analyzer = TypeScriptAnalyzer()
        self.mock_llm = MagicMock(spec=OpenAI)

    def test_understand_and_categorize_error(self):
        # Mock LLM response
        self.mock_llm.predict.return_value = '{"category": "TypeError", "location": "line 5", "explanation": "Undefined property access"}'
        
        error_message = "TypeError: Cannot read property 'x' of undefined"
        file_paths = ["/path/to/test.ts"]
        
        result = self.analyzer.understand_and_categorize_error(
            error_message, 
            file_paths, 
            llm=self.mock_llm
        )
        
        self.assertEqual(result['category'], 'TypeError')
        self.assertEqual(result['location'], 'line 5')
        self.assertEqual(result['explanation'], 'Undefined property access')

    def test_generate_fix_instructions(self):
        # Mock LLM response
        self.mock_llm.predict.return_value = '{"instructions": "Add null check before accessing property", "code_snippets": "if (obj && obj.x) { // use obj.x }"}'
        
        result = self.analyzer.generate_fix_instructions(
            "TypeError", 
            "line 5", 
            "Undefined property access", 
            ["/path/to/test.ts"], 
            llm=self.mock_llm
        )
        
        self.assertEqual(result['instructions'], 'Add null check before accessing property')
        self.assertTrue('code_snippets' in result)

    def test_apply_fixes(self):
        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            temp_file.write("original code")
            temp_file_path = temp_file.name
        
        try:
            # Apply fix
            self.analyzer.apply_fixes(
                [temp_file_path], 
                "Add null check", 
                "if (obj && obj.x) { // use obj.x }"
            )
            
            # Verify file contents
            with open(temp_file_path, 'r') as f:
                content = f.read()
                self.assertEqual(content, "if (obj && obj.x) { // use obj.x }")
        
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)

    @patch('analyzers.typescript_analyzer.TypeScriptAnalyzer.understand_and_categorize_error')
    @patch('analyzers.typescript_analyzer.TypeScriptAnalyzer.generate_fix_instructions')
    @patch('analyzers.typescript_analyzer.TypeScriptAnalyzer.apply_fixes')
    def test_generate_and_apply_fixes_workflow(
        self, 
        mock_apply_fixes, 
        mock_generate_fix_instructions, 
        mock_understand_error
    ):
        # Setup mock returns
        mock_understand_error.return_value = {
            'category': 'TypeError', 
            'location': 'line 5', 
            'explanation': 'Undefined property access'
        }
        mock_generate_fix_instructions.return_value = {
            'instructions': 'Add null check', 
            'code_snippets': 'if (obj && obj.x) { // use obj.x }'
        }
        
        error_message = "TypeError: Cannot read property 'x' of undefined"
        file_paths = ["/path/to/test.ts"]
        
        # Run the full workflow
        self.analyzer.generate_and_apply_fixes(
            error_message, 
            file_paths, 
            llm=self.mock_llm
        )
        
        # Verify method calls
        mock_understand_error.assert_called_once_with(
            error_message, 
            file_paths, 
            llm=self.mock_llm
        )
        mock_generate_fix_instructions.assert_called_once()
        mock_apply_fixes.assert_called_once()

    def test_restore_file(self):
        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            temp_file.write("original code")
            temp_file_path = temp_file.name
        
        try:
            # Apply fix
            self.analyzer.apply_fixes(
                [temp_file_path], 
                "Add null check", 
                "if (obj && obj.x) { // use obj.x }"
            )
            
            # Restore file
            self.analyzer.restore_file(temp_file_path)
            
            # Verify file contents
            with open(temp_file_path, 'r') as f:
                content = f.read()
                self.assertEqual(content, "original code")
        
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)

class MockLLM(BaseLLM):
    def __call__(self, prompt: str) -> str:
        # Simulate LLM response based on the prompt
        if "Categorize the error" in prompt:
            return '{"category": "syntax_error", "location": "line 10", "explanation": "Missing semicolon"}'
        elif "Generate detailed instructions" in prompt:
            return '{"instructions": "Add missing semicolon", "code_snippets": "const x = 5;"}'
        return ""

class TestTypeScriptAnalyzer(unittest.TestCase):
    def test_understand_and_categorize_error(self):
        """Test the error categorization method."""
        analyzer = TypeScriptAnalyzer()
        mock_llm = MockLLM()
        
        error_message = "Syntax error in file"
        file_paths = ["/path/to/file.ts"]
        
        result = analyzer.understand_and_categorize_error(error_message, file_paths, mock_llm)
        
        self.assertEqual(result, {
            "category": "syntax_error", 
            "location": "line 10", 
            "explanation": "Missing semicolon"
        })

    def test_generate_fix_instructions(self):
        """Test the fix instructions generation method."""
        analyzer = TypeScriptAnalyzer()
        mock_llm = MockLLM()
        
        result = analyzer.generate_fix_instructions(
            "syntax_error", 
            "line 10", 
            "Missing semicolon", 
            ["/path/to/file.ts"], 
            mock_llm
        )
        
        self.assertEqual(result, {
            "instructions": "Add missing semicolon", 
            "code_snippets": "const x = 5;"
        })

    @patch('tools.driver_tools.write_file')
    def test_apply_fixes(self, mock_write_file):
        """Test the method for applying fixes."""
        analyzer = TypeScriptAnalyzer()
        
        file_paths = ["/path/to/file.ts"]
        code_snippets = "const x = 5;"
        
        analyzer.apply_fixes(file_paths, code_snippets)
        
        # Verify write_file was called with correct arguments
        mock_write_file.assert_called_once_with("/path/to/file.ts", "const x = 5;")

    @patch('tools.driver_tools.write_file')
    def test_generate_and_apply_fixes(self, mock_write_file):
        """Test the end-to-end fix generation and application method."""
        analyzer = TypeScriptAnalyzer()
        mock_llm = MockLLM()
        
        analyzer.generate_and_apply_fixes(
            "Syntax error in file", 
            ["/path/to/file.ts"], 
            mock_llm
        )
        
        # Verify write_file was called with the generated code snippet
        mock_write_file.assert_called_once_with("/path/to/file.ts", "const x = 5;")

if __name__ == '__main__':
    unittest.main()