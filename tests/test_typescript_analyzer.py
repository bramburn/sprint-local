import unittest
from analyzers import TypeScriptAnalyzer

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
import * as React from 'react';
import DefaultExport from 'module';
import { Type1, Type2 } from './types';
"""
        result = self.analyzer.analyze_code(code)
        
        # Check if the imports contain the expected modules
        module_names = {imp['module'] for imp in result.imports}
        self.assertIn('@angular/core', module_names)
        self.assertIn('react', module_names)
        self.assertIn('module', module_names)
        self.assertIn('./types', module_names)

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

if __name__ == '__main__':
    unittest.main()