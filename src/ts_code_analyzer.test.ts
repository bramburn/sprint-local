import { TypeScriptCodeAnalyzer } from './ts_code_analyzer';

describe('TypeScriptCodeAnalyzer', () => {
    const analyzer = new TypeScriptCodeAnalyzer();

    test('extract function signatures in JS', () => {
        const code = `
        /**
         * Calculates the tax based on the income.
         * @param income - The income amount.
         * @returns The tax amount.
         */
        function calculateTax(income) {
            return income * 0.2;
        }
        `;
        const codeStructure = analyzer.analyzeCode(code, "sample.js");
        
        expect(codeStructure.functions.length).toBe(1);
        const func = codeStructure.functions[0];
        expect(func.name).toBe('calculateTax');
        expect(func.docstring).toBe('Calculates the tax based on the income.');
        expect(func.args).toEqual([{name: 'income', type: 'any'}]);
        expect(func.returns).toBe('void');
        expect(func.is_async).toBe(false);
    });

    test('extract function signatures in TS', () => {
        const code = `
        /**
         * Calculates the tax based on the income.
         * @param income - The income amount.
         * @returns The tax amount.
         */
        function calculateTax(income: number): number {
            return income * 0.2;
        }
        `;
        const codeStructure = analyzer.analyzeCode(code, "sample.ts");
        
        expect(codeStructure.functions.length).toBe(1);
        const func = codeStructure.functions[0];
        expect(func.name).toBe('calculateTax');
        expect(func.docstring).toBe('Calculates the tax based on the income.');
        expect(func.args).toEqual([{name: 'income', type: 'number'}]);
        expect(func.returns).toBe('number');
        expect(func.is_async).toBe(false);
    });

    test('extract class definitions in JS', () => {
        const code = `
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
        `;
        const codeStructure = analyzer.analyzeCode(code, "sample.js");
        
        expect(codeStructure.classes.length).toBe(1);
        const cls = codeStructure.classes[0];
        expect(cls.name).toBe('Person');
        expect(cls.docstring).toBe('Represents a person.');
        expect(cls.methods.length).toBe(2);
        
        expect(cls.methods[0].name).toBe('constructor');
        expect(cls.methods[0].docstring).toBe('Initializes a new instance of the Person class.');
        expect(cls.methods[0].args).toEqual([
            {name: 'name', type: 'any'}, 
            {name: 'age', type: 'any'}
        ]);
        expect(cls.methods[0].returns).toBe('void');
        
        expect(cls.methods[1].name).toBe('getName');
        expect(cls.methods[1].docstring).toBe('Gets the name of the person.');
        expect(cls.methods[1].args).toEqual([]);
        expect(cls.methods[1].returns).toBe('void');
    });

    test('extract class definitions in TS', () => {
        const code = `
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
        `;
        const codeStructure = analyzer.analyzeCode(code, "sample.ts");
        
        expect(codeStructure.classes.length).toBe(1);
        const cls = codeStructure.classes[0];
        expect(cls.name).toBe('Person');
        expect(cls.docstring).toBe('Represents a person.');
        expect(cls.methods.length).toBe(2);
        
        expect(cls.methods[0].name).toBe('constructor');
        expect(cls.methods[0].docstring).toBe('Initializes a new instance of the Person class.');
        expect(cls.methods[0].args).toEqual([
            {name: 'name', type: 'string'}, 
            {name: 'age', type: 'number'}
        ]);
        expect(cls.methods[0].returns).toBe('void');
        
        expect(cls.methods[1].name).toBe('getName');
        expect(cls.methods[1].docstring).toBe('Gets the name of the person.');
        expect(cls.methods[1].args).toEqual([]);
        expect(cls.methods[1].returns).toBe('string');
    });

    test('extract import statements', () => {
        const code = `
        import React from 'react';
        import { useState, useEffect } from 'react';
        import axios from 'axios';
        `;
        const codeStructure = analyzer.analyzeCode(code, "sample.ts");
        
        expect(codeStructure.imports.length).toBe(3);
        
        expect(codeStructure.imports[0].module).toBe('react');
        expect(codeStructure.imports[0].default_import).toBe('React');
        expect(codeStructure.imports[0].named_imports).toEqual([]);
        
        expect(codeStructure.imports[1].module).toBe('react');
        expect(codeStructure.imports[1].default_import).toBeNull();
        expect(codeStructure.imports[1].named_imports).toEqual(['useState', 'useEffect']);
        
        expect(codeStructure.imports[2].module).toBe('axios');
        expect(codeStructure.imports[2].default_import).toBe('axios');
        expect(codeStructure.imports[2].named_imports).toEqual([]);
    });

    test('extract variables', () => {
        const code = `
        const taxRate: number = 0.2;
        let income: number = 10000;
        var name: string;
        `;
        const codeStructure = analyzer.analyzeCode(code, "sample.ts");
        
        expect(codeStructure.variables).toEqual(['taxRate', 'income', 'name']);
    });
});
