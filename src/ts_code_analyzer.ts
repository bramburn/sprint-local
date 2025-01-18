import * as ts from 'typescript';
import * as fs from 'fs';

export interface CodeStructure {
    functions: {
        name: string;
        line: number;
        docstring: string;
        args: { name: string; type: string }[];
        returns: string;
        is_async: boolean;
    }[];
    classes: {
        name: string;
        line: number;
        docstring: string;
        methods: {
            name: string;
            line: number;
            docstring: string;
            args: { name: string; type: string }[];
            returns: string;
        }[];
    }[];
    imports: {
        module: string;
        names: string[];
    }[];
    variables: {
        name: string;
        type: string;
        line: number;
    }[];
}

export class TypeScriptCodeAnalyzer {
    private sourceFile: ts.SourceFile | null = null;

    public analyzeCode(code: string, filePath: string = 'input.ts'): CodeStructure {
        console.error('Starting code analysis');
        console.error('Input code:', code);

        // Normalize the code by removing leading/trailing whitespace and extra newlines
        code = code.trim().replace(/^\s+|\s+$/g, '');

        console.error('Normalized code:', code);

        try {
            // Create source file with full parsing
            this.sourceFile = ts.createSourceFile(
                filePath, 
                code, 
                ts.ScriptTarget.Latest, 
                true,  // Set to true to parse comments
                ts.ScriptKind.TS  // Explicitly set script kind
            );

            // Create compiler options
            const compilerOptions: ts.CompilerOptions = {
                noEmit: true,
                allowJs: true,
                target: ts.ScriptTarget.ES5,
                module: ts.ModuleKind.CommonJS,
                experimentalDecorators: true,
                emitDecoratorMetadata: true,
                esModuleInterop: true,
                skipLibCheck: true,
                noResolve: false,
                allowSyntheticDefaultImports: true,
                moduleResolution: ts.ModuleResolutionKind.NodeJs,
                types: ["node"],
                typeRoots: ["./node_modules/@types"],
                jsx: ts.JsxEmit.None,
                strict: false,
                noImplicitAny: false,
                noUnusedLocals: false,
                noUnusedParameters: false,
                baseUrl: ".",
                paths: {
                    "*": ["node_modules/*"]
                }
            };

            // Create a program with custom host
            const host = ts.createCompilerHost(compilerOptions);

            // Override host functions to handle library resolution
            const originalGetSourceFile = host.getSourceFile;
            host.getSourceFile = (fileName: string, languageVersion: ts.ScriptTarget) => {
                // Handle lib files
                if (fileName.startsWith('lib.')) {
                    const libContent = `
                        interface Array<T> {}
                        interface Boolean {}
                        interface Function {}
                        interface IArguments {}
                        interface Number {}
                        interface Object {}
                        interface RegExp {}
                        interface String {}
                        interface Promise<T> {}
                        declare var console: { log(msg: any): void; };
                        declare function decorator(target: any): any;
                        declare var module: { exports: any };
                        declare var require: Function;
                        declare var process: any;
                    `;
                    return ts.createSourceFile(fileName, libContent, languageVersion);
                }
                return originalGetSourceFile(fileName, languageVersion);
            };

            // Override module resolution
            host.resolveModuleNames = (moduleNames: string[], containingFile: string) => {
                return moduleNames.map(() => ({
                    resolvedFileName: 'dummy.d.ts',
                    extension: '.d.ts',
                    isExternalLibraryImport: false,
                    packageId: undefined
                }));
            };

            const program = ts.createProgram([filePath], compilerOptions, host);

            const diagnostics = ts.getPreEmitDiagnostics(program);
            const filteredDiagnostics = diagnostics.filter(d => {
                // Filter out module resolution errors and decorator-related errors
                if (d.code === 2307) return false;  // Cannot find module
                if (d.code === 1479) return false;  // Cannot use imports, exports, or module augmentations
                if (d.code === 1240) return false;  // Decorators are not valid here
                if (d.code === 1241) return false;  // Decorators can only be used in TypeScript files
                if (d.code === 1219) return false;  // Experimental decorators warning
                if (d.code === 2339) return false;  // Property does not exist on type
                if (d.code === 2304) return false;  // Cannot find name
                if (d.code === 2503) return false;  // Cannot find namespace
                if (d.code === 2552) return false;  // Cannot find name in scope
                if (d.code === 2318) return false;  // Cannot find global type
                if (d.code === 2688) return false;  // Cannot find type definition file
                if (d.code === 2691) return false;  // Cannot find lib definition
                if (d.code === 2694) return false;  // Cannot find lib file
                if (d.code === 2300) return false;  // Duplicate identifier
                if (d.code === 2451) return false;  // Cannot redeclare block-scoped variable
                if (d.code === 2749) return false;  // Cannot find global value
                if (d.code === 2669) return false;  // Augmentations for the global scope can only be directly nested
                if (d.code === 2304) return false;  // Cannot find name
                if (d.code === 2503) return false;  // Cannot find namespace
                if (d.code === 2552) return false;  // Cannot find name in scope
                if (d.code === 1206) return false;  // Decorators are not valid here
                if (d.code === 1238) return false;  // Unable to resolve signature of class decorator
                if (d.code === 1239) return false;  // Unable to resolve signature of parameter decorator
                if (d.code === 1240) return false;  // Unable to resolve signature of property decorator
                if (d.code === 1241) return false;  // Unable to resolve signature of method decorator
                if (d.code === 1242) return false;  // Unable to resolve signature of class decorator
                if (d.code === 1270) return false;  // Decorator function return type is not assignable
                return true;
            });

            if (filteredDiagnostics.length > 0) {
                const errors = filteredDiagnostics.map(diagnostic => {
                    const message = ts.flattenDiagnosticMessageText(diagnostic.messageText, '\n');
                    return message;
                }).join('\n');
                throw new Error(`TypeScript compilation errors:\n${errors}`);
            }

            const codeStructure: CodeStructure = {
                functions: [],
                classes: [],
                imports: [],
                variables: []
            };

            console.error('Analyzing source file...');
            this._analyzeSourceFile(this.sourceFile, codeStructure);

            console.error('Detected functions:', JSON.stringify(codeStructure.functions, null, 2));
            return codeStructure;
        } catch (error: unknown) {
            console.error('Error analyzing code:', error);
            if (error instanceof Error) {
                throw new Error(`Failed to analyze TypeScript code: ${error.message}`);
            } else {
                throw new Error('Failed to analyze TypeScript code: Unknown error');
            }
        }
    }

    private _analyzeSourceFile(sourceFile: ts.SourceFile, codeStructure: CodeStructure) {
        // Traverse all nodes in the source file
        const visit = (node: ts.Node) => {
            // Log each node type for debugging
            console.error(`Node type: ${ts.SyntaxKind[node.kind]}`);

            // Analyze imports
            if (ts.isImportDeclaration(node)) {
                console.error('Found import declaration');
                this._analyzeImportDeclaration(node, codeStructure);
            }

            // Analyze function declarations
            if (ts.isFunctionDeclaration(node)) {
                console.error('Found function declaration');
                this._analyzeFunctionDeclaration(node, codeStructure);
            }
            
            // Analyze variable statements that might contain arrow functions
            if (ts.isVariableStatement(node)) {
                console.error('Found variable statement');
                this._analyzeVariableStatement(node, codeStructure);
            }

            // Analyze class declarations
            if (ts.isClassDeclaration(node)) {
                console.error('Found class declaration');
                this._analyzeClassDeclaration(node, codeStructure);
            }

            // Continue traversing child nodes
            ts.forEachChild(node, visit);
        };

        visit(sourceFile);
    }

    private _analyzeImportDeclaration(node: ts.ImportDeclaration, codeStructure: CodeStructure) {
        const moduleSpecifier = node.moduleSpecifier;
        if (ts.isStringLiteral(moduleSpecifier)) {
            const moduleName = moduleSpecifier.text;
            const importClause = node.importClause;
            const names: string[] = [];

            if (importClause) {
                // Handle default imports
                if (importClause.name) {
                    names.push(importClause.name.text);
                }

                // Handle named imports
                if (importClause.namedBindings) {
                    if (ts.isNamedImports(importClause.namedBindings)) {
                        names.push(...importClause.namedBindings.elements.map(e => e.name.text));
                    } else if (ts.isNamespaceImport(importClause.namedBindings)) {
                        names.push(importClause.namedBindings.name.text);
                    }
                }
            }

            codeStructure.imports.push({
                module: moduleName,
                names: names
            });
        }
    }

    private _analyzeFunctionDeclaration(node: ts.FunctionDeclaration, codeStructure: CodeStructure) {
        // Ensure the function has a name
        const functionName = node.name ? node.name.getText() : 'anonymous';
        console.error(`Analyzing function: ${functionName}`);

        // Get the line number
        const line = this.sourceFile 
            ? this.sourceFile.getLineAndCharacterOfPosition(node.pos).line + 1 
            : 0;

        // Check if the function is async
        const isAsync = node.modifiers?.some(mod => 
            mod.kind === ts.SyntaxKind.AsyncKeyword
        ) || false;

        const functionInfo = {
            name: functionName,
            line: line,
            docstring: this._extractDocstring(node),
            args: node.parameters.map(param => ({
                name: param.name.getText(),
                type: param.type ? param.type.getText() : 'any'
            })),
            returns: node.type ? node.type.getText() : 'void',
            is_async: isAsync
        };

        console.error('Adding function:', JSON.stringify(functionInfo, null, 2));
        codeStructure.functions.push(functionInfo);
    }

    private _analyzeVariableStatement(node: ts.VariableStatement, codeStructure: CodeStructure) {
        node.declarationList.declarations.forEach(declaration => {
            // Add variable to the variables list
            const variableName = declaration.name.getText();
            const variableType = declaration.type ? declaration.type.getText() : 'any';
            const line = this.sourceFile 
                ? this.sourceFile.getLineAndCharacterOfPosition(declaration.pos).line + 1 
                : 0;

            codeStructure.variables.push({
                name: variableName,
                type: variableType,
                line: line
            });

            // Check if the initializer exists and is an arrow function
            if (declaration.initializer && ts.isArrowFunction(declaration.initializer)) {
                const functionName = declaration.name.getText();
                const line = this.sourceFile 
                    ? this.sourceFile.getLineAndCharacterOfPosition(declaration.pos).line + 1 
                    : 0;

                const arrowFunction = declaration.initializer;
                const isAsync = arrowFunction.modifiers?.some(mod => 
                    mod.kind === ts.SyntaxKind.AsyncKeyword
                ) || false;

                const functionInfo = {
                    name: functionName,
                    line: line,
                    docstring: this._extractDocstring(declaration),
                    args: arrowFunction.parameters.map(param => ({
                        name: param.name.getText(),
                        type: param.type ? param.type.getText() : 'any'
                    })),
                    returns: arrowFunction.type 
                        ? arrowFunction.type.getText() 
                        : (arrowFunction.body.kind === ts.SyntaxKind.Block ? 'void' : 'any'),
                    is_async: isAsync
                };

                console.error('Adding arrow function:', JSON.stringify(functionInfo, null, 2));
                codeStructure.functions.push(functionInfo);
            }
        });
    }

    private _analyzeClassDeclaration(node: ts.ClassDeclaration, codeStructure: CodeStructure) {
        // Ensure the class has a name
        const className = node.name ? node.name.getText() : 'anonymous';
        console.error(`Analyzing class: ${className}`);

        // Get the line number
        const line = this.sourceFile 
            ? this.sourceFile.getLineAndCharacterOfPosition(node.pos).line + 1 
            : 0;

        console.error(`Class line number: ${line}`);
        console.error(`Number of class members: ${node.members.length}`);

        // Analyze class methods
        const methods = node.members
            .filter(member => 
                ts.isMethodDeclaration(member) || 
                ts.isConstructorDeclaration(member)
            )
            .map(method => {
                const methodName = ts.isConstructorDeclaration(method) 
                    ? 'constructor' 
                    : method.name.getText();

                const methodLine = this.sourceFile 
                    ? this.sourceFile.getLineAndCharacterOfPosition(method.pos).line + 1 
                    : 0;

                console.error(`Method: ${methodName}, Line: ${methodLine}`);

                return {
                    name: methodName,
                    line: methodLine,
                    docstring: this._extractDocstring(method),
                    args: method.parameters.map(param => ({
                        name: param.name.getText(),
                        type: param.type ? param.type.getText() : 'any'
                    })),
                    returns: ts.isMethodDeclaration(method) && method.type 
                        ? method.type.getText() 
                        : 'void'
                };
            });

        console.error('Extracted methods:', JSON.stringify(methods, null, 2));

        // Create class info
        const classInfo = {
            name: className,
            line: line,
            docstring: this._extractDocstring(node),
            methods: methods
        };

        console.error('Adding class:', JSON.stringify(classInfo, null, 2));
        codeStructure.classes.push(classInfo);
    }

    private _extractDocstring(node: ts.Node): string {
        if (!this.sourceFile) return '';

        // Extract JSDoc comments or leading comments
        const comments = ts.getLeadingCommentRanges(this.sourceFile.getFullText(), node.pos);
        if (comments && comments.length > 0) {
            const commentText = this.sourceFile.getFullText().substring(
                comments[0].pos,
                comments[0].end
            ).trim();
            return commentText;
        }
        return '';
    }
}

// Main execution
if (require.main === module) {
    // Ensure a file path is provided
    if (process.argv.length < 3) {
        console.error('Please provide a file path');
        process.exit(1);
    }

    const filePath = process.argv[2];

    try {
        // Read the file contents
        const code = fs.readFileSync(filePath, 'utf-8');

        // Create and run the analyzer
        const analyzer = new TypeScriptCodeAnalyzer();
        const result = analyzer.analyzeCode(code, filePath);

        // Output the result as JSON
        console.log(JSON.stringify(result, null, 2));
    } catch (error) {
        console.error('Error analyzing TypeScript code:', error);
        process.exit(1);
    }
}
