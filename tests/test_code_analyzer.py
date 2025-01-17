import pytest
from code_analyzer import CodeAnalyzer

def test_code_analysis_basic():
    """
    Test basic code analysis functionality.
    Verify extraction of classes, functions, imports, and variables.
    """
    analyzer = CodeAnalyzer()
    code = '''
import os
from typing import List

class Example:
    """Example class docstring"""
    def __init__(self, x: int):
        """Constructor docstring"""
        self.x = x

    def method(self, arg: str) -> None:
        """Method docstring"""
        pass

def standalone_function(y: int) -> str:
    """Function docstring"""
    z = y * 2
    return str(z)

global_var = 42
'''
    
    structure = analyzer.analyze_code(code)
    
    # Test class analysis
    assert len(structure.classes) == 1
    assert structure.classes[0]['name'] == 'Example'
    assert structure.classes[0]['docstring'] == 'Example class docstring'
    assert len(structure.classes[0]['methods']) == 2
    
    # Test method analysis
    methods = structure.classes[0]['methods']
    init_method = methods[0]
    assert init_method['name'] == '__init__'
    assert init_method['args'][0]['name'] == 'x'
    assert init_method['args'][0]['annotation'] == 'int'
    
    # Test function analysis
    assert len(structure.functions) == 1
    func = structure.functions[0]
    assert func['name'] == 'standalone_function'
    assert func['docstring'] == 'Function docstring'
    assert func['args'][0]['name'] == 'y'
    assert func['args'][0]['annotation'] == 'int'
    assert func['returns'] == 'str'
    
    # Test import analysis
    assert len(structure.imports) == 2
    assert 'os' in structure.imports
    assert 'typing.List' in structure.imports
    
    # Test variable analysis
    assert len(structure.variables) == 1
    assert 'global_var' in structure.variables

def test_empty_code_analysis():
    """
    Test code analysis with empty input.
    Verify no errors and empty structure returned.
    """
    analyzer = CodeAnalyzer()
    structure = analyzer.analyze_code('')
    
    assert len(structure.classes) == 0
    assert len(structure.functions) == 0
    assert len(structure.imports) == 0
    assert len(structure.variables) == 0

def test_complex_code_analysis():
    """
    Test code analysis with more complex code structure.
    Verify handling of nested classes, multiple imports, etc.
    """
    analyzer = CodeAnalyzer()
    code = '''
import sys
from collections import defaultdict
from typing import Dict, Any

class OuterClass:
    """Outer class docstring"""
    class InnerClass:
        """Inner class docstring"""
        def inner_method(self):
            """Inner method docstring"""
            pass

    def outer_method(self, param1: Dict[str, Any]) -> bool:
        """Outer method docstring"""
        return True

def utility_function(x: List[int]) -> int:
    """Utility function docstring"""
    return sum(x)

multiple_var1 = 10
multiple_var2 = "string"
'''
    
    structure = analyzer.analyze_code(code)
    
    # Test nested class analysis
    assert len(structure.classes) == 1
    outer_class = structure.classes[0]
    assert outer_class['name'] == 'OuterClass'
    assert len(outer_class['methods']) == 2  # outer_method and InnerClass
    
    # Test import analysis
    assert len(structure.imports) == 3
    assert 'sys' in structure.imports
    assert 'collections.defaultdict' in structure.imports
    assert 'typing.Dict' in structure.imports
    
    # Test multiple variables
    assert len(structure.variables) == 2
    assert 'multiple_var1' in structure.variables
    assert 'multiple_var2' in structure.variables
