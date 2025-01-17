import pytest
from ts_code_analyzer import TypeScriptCodeAnalyzer

def test_extract_function_signatures_js():
    code = """
    /**
     * Calculates the tax based on the income.
     * @param income - The income amount.
     * @returns The tax amount.
     */
    function calculateTax(income) {
        return income * 0.2;
    }
    """
    analyzer = TypeScriptCodeAnalyzer()
    code_structure = analyzer.analyze_code(code, "sample.js")
    
    assert len(code_structure['functions']) == 1
    func = code_structure['functions'][0]
    assert func['name'] == 'calculateTax'
    assert func['docstring'] == 'Calculates the tax based on the income.'
    assert func['args'] == [{'name': 'income', 'type': 'any'}]
    assert func['returns'] == 'void'
    assert not func['is_async']

def test_extract_function_signatures_ts():
    code = """
    /**
     * Calculates the tax based on the income.
     * @param income - The income amount.
     * @returns The tax amount.
     */
    function calculateTax(income: number): number {
        return income * 0.2;
    }
    """
    analyzer = TypeScriptCodeAnalyzer()
    code_structure = analyzer.analyze_code(code, "sample.ts")
    
    assert len(code_structure['functions']) == 1
    func = code_structure['functions'][0]
    assert func['name'] == 'calculateTax'
    assert func['docstring'] == 'Calculates the tax based on the income.'
    assert func['args'] == [{'name': 'income', 'type': 'number'}]
    assert func['returns'] == 'number'
    assert not func['is_async']

def test_extract_class_definitions_js():
    code = """
    /**
     * Represents a person.
     */
    class Person {
        /**
         * Initializes a new instance of the Person class.
         * @param name - The name of the person.
         * @param age - The age of the person.
         */
        constructor(name, age) {
            this.name = name;
            this.age = age;
        }

        /**
         * Gets the name of the person.
         * @returns The name of the person.
         */
        getName() {
            return this.name;
        }
    }
    """
    analyzer = TypeScriptCodeAnalyzer()
    code_structure = analyzer.analyze_code(code, "sample.js")
    
    assert len(code_structure['classes']) == 1
    cls = code_structure['classes'][0]
    assert cls['name'] == 'Person'
    assert cls['docstring'] == 'Represents a person.'
    assert len(cls['methods']) == 2
    
    assert cls['methods'][0]['name'] == 'constructor'
    assert cls['methods'][0]['args'] == [
        {'name': 'name', 'type': 'any'}, 
        {'name': 'age', 'type': 'any'}
    ]
    assert cls['methods'][0]['returns'] == 'void'
    
    assert cls['methods'][1]['name'] == 'getName'
    assert cls['methods'][1]['args'] == []
    assert cls['methods'][1]['returns'] == 'void'

def test_extract_class_definitions_ts():
    code = """
    /**
     * Represents a person.
     */
    class Person {
        name: string;
        age: number;

        /**
         * Initializes a new instance of the Person class.
         * @param name - The name of the person.
         * @param age - The age of the person.
         */
        constructor(name: string, age: number) {
            this.name = name;
            this.age = age;
        }

        /**
         * Gets the name of the person.
         * @returns The name of the person.
         */
        getName(): string {
            return this.name;
        }
    }
    """
    analyzer = TypeScriptCodeAnalyzer()
    code_structure = analyzer.analyze_code(code, "sample.ts")
    
    assert len(code_structure['classes']) == 1
    cls = code_structure['classes'][0]
    assert cls['name'] == 'Person'
    assert cls['docstring'] == 'Represents a person.'
    assert len(cls['methods']) == 2
    
    assert cls['methods'][0]['name'] == 'constructor'
    assert cls['methods'][0]['args'] == [
        {'name': 'name', 'type': 'string'}, 
        {'name': 'age', 'type': 'number'}
    ]
    assert cls['methods'][0]['returns'] == 'void'
    
    assert cls['methods'][1]['name'] == 'getName'
    assert cls['methods'][1]['args'] == []
    assert cls['methods'][1]['returns'] == 'string'

def test_extract_import_statements():
    code = """
    import React from 'react';
    import { useState, useEffect } from 'react';
    import axios from 'axios';
    """
    analyzer = TypeScriptCodeAnalyzer()
    code_structure = analyzer.analyze_code(code, "sample.ts")
    
    assert len(code_structure['imports']) == 3
    
    assert code_structure['imports'][0]['module'] == 'react'
    assert code_structure['imports'][0]['default_import'] == 'React'
    assert code_structure['imports'][0]['named_imports'] == []
    
    assert code_structure['imports'][1]['module'] == 'react'
    assert code_structure['imports'][1]['default_import'] is None
    assert code_structure['imports'][1]['named_imports'] == ['useState', 'useEffect']
    
    assert code_structure['imports'][2]['module'] == 'axios'
    assert code_structure['imports'][2]['default_import'] == 'axios'
    assert code_structure['imports'][2]['named_imports'] == []

def test_extract_variables():
    code = """
    const taxRate: number = 0.2;
    let income: number = 10000;
    var name: string;
    """
    analyzer = TypeScriptCodeAnalyzer()
    code_structure = analyzer.analyze_code(code, "sample.ts")
    
    assert set(code_structure['variables']) == {'taxRate', 'income', 'name'}
