import unittest
from analyzers import PythonAnalyzer

class TestPythonAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = PythonAnalyzer()

    def test_analyze_empty_code(self):
        result = self.analyzer.analyze_code("")
        self.assertEqual(result.classes, [])
        self.assertEqual(result.functions, [])
        self.assertEqual(result.imports, [])
        self.assertEqual(result.variables, [])

    def test_analyze_basic_class(self):
        code = """
class TestClass:
    def __init__(self, x):
        self.x = x
        
    def test_method(self, y):
        return self.x + y
"""
        result = self.analyzer.analyze_code(code)
        
        self.assertEqual(len(result.classes), 1)
        test_class = result.classes[0]
        self.assertEqual(test_class['name'], 'TestClass')
        self.assertEqual(len(test_class['methods']), 2)
        
        # Check methods
        method_names = {m['name'] for m in test_class['methods']}
        self.assertEqual(method_names, {'__init__', 'test_method'})

    def test_analyze_functions(self):
        code = """
def test_func1(x, y):
    return x + y

@decorator
def test_func2(a, *args, **kwargs):
    pass
"""
        result = self.analyzer.analyze_code(code)
        
        self.assertEqual(len(result.functions), 2)
        func_names = {f['name'] for f in result.functions}
        self.assertEqual(func_names, {'test_func1', 'test_func2'})
        
        # Check decorators
        decorated_func = next(f for f in result.functions if f['name'] == 'test_func2')
        self.assertEqual(decorated_func['decorators'], ['decorator'])

    def test_analyze_imports(self):
        code = """
import os
from typing import List, Optional
from module.submodule import Class1, Class2
"""
        result = self.analyzer.analyze_code(code)
        
        expected_imports = {
            'os',
            'typing',
            'module.submodule'
        }
        
        imports_set = set(result.imports)
        self.assertTrue(all(imp in imports_set for imp in expected_imports))

    def test_analyze_variables(self):
        code = """
x = 1
y, z = 2, 3
CONSTANT = "test"
"""
        result = self.analyzer.analyze_code(code)
        
        expected_variables = {'x', 'y', 'z', 'CONSTANT'}
        self.assertEqual(set(result.variables), expected_variables)

    def test_invalid_code(self):
        with self.assertRaises(ValueError):
            self.analyzer.analyze_code("class Invalid:")

if __name__ == '__main__':
    unittest.main() 