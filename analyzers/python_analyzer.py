import ast
from typing import Dict, List, Optional, Any

from .base import BaseAnalyzer, CodeStructure

class PythonAnalyzer(BaseAnalyzer):
    """Analyzer for Python source code using the ast module."""

    def analyze_code(self, code: str, file_path: Optional[str] = None) -> CodeStructure:
        """
        Analyze Python code and extract its structure.
        
        Args:
            code: Python source code to analyze
            file_path: Optional path to the source file
            
        Returns:
            CodeStructure containing the analyzed components
        """
        try:
            tree = ast.parse(code)
            visitor = PythonAstVisitor()
            visitor.visit(tree)
            
            return CodeStructure(
                classes=visitor.classes,
                functions=visitor.functions,
                imports=visitor.imports,
                variables=visitor.variables
            )
        except SyntaxError as e:
            raise ValueError(f"Invalid Python code: {str(e)}")

class PythonAstVisitor(ast.NodeVisitor):
    """AST visitor to extract code structure from Python source."""
    
    def __init__(self):
        self.classes: List[Dict] = []
        self.functions: List[Dict] = []
        self.imports: List[str] = []
        self.variables: List[str] = []
        self._current_class: Optional[Dict] = None  # Track current class context
        
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Extract class definitions."""
        class_info = {
            'name': node.name,
            'methods': [],
            'bases': [base.id for base in node.bases if isinstance(base, ast.Name)],
            'decorators': [self._get_decorator_name(d) for d in node.decorator_list],
            'lineno': node.lineno
        }
        
        # Save the previous class context
        previous_class = self._current_class
        self._current_class = class_info
        
        # Visit class body
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                method_info = self._get_function_info(item)
                class_info['methods'].append(method_info)
                
        self.classes.append(class_info)
        
        # Restore previous class context
        self._current_class = previous_class
        
        self.generic_visit(node)
        
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Extract function definitions."""
        # Only add non-method functions
        if self._current_class is None:
            self.functions.append(self._get_function_info(node))
        
        self.generic_visit(node)
        
    def visit_Import(self, node: ast.Import) -> None:
        """Extract import statements."""
        for name in node.names:
            # Preserve the full module path
            self.imports.append(name.name)
        
    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Extract from-import statements."""
        if node.module:
            # Preserve the full module path
            self.imports.append(node.module)
                
    def visit_Assign(self, node: ast.Assign) -> None:
        """Extract variable assignments."""
        for target in node.targets:
            # Handle tuple unpacking
            if isinstance(target, ast.Tuple):
                for elt in target.elts:
                    if isinstance(elt, ast.Name):
                        self.variables.append(elt.id)
            # Handle single variable assignments
            elif isinstance(target, ast.Name):
                self.variables.append(target.id)
        
        self.generic_visit(node)
        
    def _get_function_info(self, node: ast.FunctionDef) -> Dict[str, Any]:
        """Helper to extract function information."""
        return {
            'name': node.name,
            'args': self._get_arguments(node.args),
            'decorators': [self._get_decorator_name(d) for d in node.decorator_list],
            'lineno': node.lineno
        }
        
    def _get_arguments(self, args: ast.arguments) -> List[str]:
        """Helper to extract function arguments."""
        arg_list = []
        
        # Add positional args
        for arg in args.posonlyargs + args.args:
            arg_list.append(arg.arg)
            
        # Add varargs if present
        if args.vararg:
            arg_list.append(f"*{args.vararg.arg}")
            
        # Add keyword args
        for arg in args.kwonlyargs:
            arg_list.append(arg.arg)
            
        # Add kwargs if present
        if args.kwarg:
            arg_list.append(f"**{args.kwarg.arg}")
            
        return arg_list
        
    def _get_decorator_name(self, decorator: ast.expr) -> str:
        """Helper to extract decorator names."""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Name):
                return decorator.func.id
        return str(decorator) 