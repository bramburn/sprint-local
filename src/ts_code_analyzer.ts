import * as ts from 'typescript';

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
        default_import: string | null;
        named_imports: string[];
    }[];
    variables: string[];
}

export class TypeScriptCodeAnalyzer {
    private sourceFile: ts.SourceFile | null = null;

    public analyzeCode(code: string, filePath: string): CodeStructure {
        this.sourceFile = ts.createSourceFile(filePath, code, ts.ScriptTarget.Latest, true);
        const codeStructure: CodeStructure = {
            functions: [],
            classes: [],
            imports: [],
            variables: []
        };

        this._analyzeNode(this.sourceFile, codeStructure);

        return codeStructure;
    }

    private _analyzeNode(node: ts.Node, codeStructure: CodeStructure) {
        // Ensure sourceFile is set
        if (!this.sourceFile) {
            return;
        }

        // Function and Arrow Function Analysis
        if (ts.isFunctionDeclaration(node) || ts.isArrowFunction(node)) {
            const name = node.name ? node.name.getText() : 'anonymous';
            const line = node.getStart(this.sourceFile, false) + 1;
            const docstring = this._cleanDocstring(this._getDocstring(node));
            const args = node.parameters.map(param => ({
                name: param.name.getText(),
                type: param.type ? param.type.getText() : 'any'
            }));
            const returns = node.type ? node.type.getText() : 'void';
            const is_async = node.modifiers?.some(mod => 
                mod.kind === ts.SyntaxKind.AsyncKeyword
            ) || false;

            codeStructure.functions.push({ 
                name, 
                line, 
                docstring, 
                args, 
                returns,
                is_async 
            });
        }
        
        // Class Declaration Analysis
        if (ts.isClassDeclaration(node)) {
            const name = node.name ? node.name.getText() : 'anonymous';
            const line = node.getStart(this.sourceFile, false) + 1;
            const docstring = this._cleanDocstring(this._getDocstring(node));
            const methods: any[] = [];

            node.members.forEach(member => {
                if (ts.isMethodDeclaration(member) || ts.isConstructorDeclaration(member)) {
                    const methodName = member.name ? member.name.getText() : 'constructor';
                    const methodLine = member.getStart(this.sourceFile!, false) + 1;
                    const methodDocstring = this._cleanDocstring(this._getDocstring(member));
                    const methodArgs = member.parameters.map(param => ({
                        name: param.name.getText(),
                        type: param.type ? param.type.getText() : 'any'
                    }));
                    const methodReturns = member.type ? member.type.getText() : 'void';

                    methods.push({
                        name: methodName,
                        line: methodLine,
                        docstring: methodDocstring,
                        args: methodArgs,
                        returns: methodReturns
                    });
                }
            });

            codeStructure.classes.push({
                name,
                line,
                docstring,
                methods
            });
        }

        // Import Declaration Analysis
        if (ts.isImportDeclaration(node)) {
            const module = node.moduleSpecifier.getText().replace(/['"]/g, '');
            const namedImports: string[] = [];
            let defaultImport: string | null = null;

            if (node.importClause) {
                if (node.importClause.namedBindings && ts.isNamedImports(node.importClause.namedBindings)) {
                    node.importClause.namedBindings.elements.forEach(element => {
                        namedImports.push(element.name.getText());
                    });
                }
                if (node.importClause.name) {
                    defaultImport = node.importClause.name.getText();
                }
            }

            codeStructure.imports.push({ 
                module, 
                default_import: defaultImport, 
                named_imports: namedImports 
            });
        }

        // Variable Declaration Analysis
        if (ts.isVariableStatement(node)) {
            node.declarationList.declarations.forEach(declaration => {
                if (ts.isIdentifier(declaration.name)) {
                    codeStructure.variables.push(declaration.name.getText());
                }
            });
        }

        ts.forEachChild(node, child => this._analyzeNode(child, codeStructure));
    }

    private _getDocstring(node: ts.Node): string {
        const jsDoc = ts.getJSDocCommentsAndTags(node);
        if (jsDoc && jsDoc.length > 0) {
            return jsDoc[0].getText();
        }
        return '';
    }

    private _cleanDocstring(docstring: string): string {
        // Remove /** and */ markers, trim whitespace, and remove leading asterisks
        return docstring
            .replace(/^\/\*\*|\*\/$/g, '')  // Remove start and end markers
            .split('\n')
            .map(line => line.replace(/^\s*\*\s*/, '').trim())  // Remove leading asterisks and whitespace
            .filter(line => line !== '')  // Remove empty lines
            .join(' ')
            .trim();
    }
}
