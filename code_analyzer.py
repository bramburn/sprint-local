import ast
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class CodeStructure:
    """
    Structured representation of code analysis results.
    
    Attributes:
        classes (List[Dict]): List of class definitions
        functions (List[Dict]): List of function definitions
        imports (List[str]): List of imported modules
        variables (List[str]): List of global variables
    """
    classes: List[Dict] = None
    functions: List[Dict] = None
    imports: List[str] = None
    variables: List[str] = None

    def __post_init__(self):
        """Initialize empty lists if not provided."""
        self.classes = self.classes or []
        self.functions = self.functions or []
        self.imports = self.imports or []
        self.variables = self.variables or []

class CodeAnalyzer:
    """
    Performs static code analysis using AST parsing.
    
    Provides detailed code structure extraction for Python files.
    """

    def analyze_code(self, code: str, file_path: Optional[str] = None) -> CodeStructure:
        """
        Analyze the structure of a given Python code.
        
        Args:
            code (str): Python source code to analyze
            file_path (Optional[str]): Path of the source file
        
        Returns:
            CodeStructure: Detailed analysis of code structure
        """
        try:
            # Parse the code using Abstract Syntax Tree
            tree = ast.parse(code)
            
            # Analyze the AST
            structure = self._analyze_ast(tree)
            
            return structure
        
        except Exception as e:
            print(f"Code analysis error: {e}")
            return CodeStructure()
    
    def _get_annotation(self, node):
        """
        Extract type annotation from a node.
        
        Args:
            node (ast.AST): Node to extract annotation from.
        
        Returns:
            str: String representation of the annotation, or None if no annotation.
        """
        if hasattr(node, 'annotation'):
            # For function arguments
            if isinstance(node.annotation, ast.Name):
                return node.annotation.id
            elif isinstance(node.annotation, ast.Attribute):
                return f"{node.annotation.value.id}.{node.annotation.attr}"
            elif isinstance(node.annotation, ast.Subscript):
                # Handle generic types like List[int], Dict[str, Any]
                if isinstance(node.annotation.value, ast.Name):
                    return f"{node.annotation.value.id}[{self._get_annotation(node.annotation.slice)}]"
                elif isinstance(node.annotation.value, ast.Attribute):
                    return f"{node.annotation.value.value.id}.{node.annotation.value.attr}[{self._get_annotation(node.annotation.slice)}]"
        
        # For function return annotations
        if hasattr(node, 'returns'):
            if node.returns is None:
                return None
            
            if isinstance(node.returns, ast.Name):
                return node.returns.id
            elif isinstance(node.returns, ast.Attribute):
                return f"{node.returns.value.id}.{node.returns.attr}"
            elif isinstance(node.returns, ast.Subscript):
                # Handle generic return types
                if isinstance(node.returns.value, ast.Name):
                    return f"{node.returns.value.id}[{self._get_annotation(node.returns.slice)}]"
                elif isinstance(node.returns.value, ast.Attribute):
                    return f"{node.returns.value.value.id}.{node.returns.value.attr}[{self._get_annotation(node.returns.slice)}]"
        
        return None

    def _analyze_ast(self, tree):
        """
        Recursively analyze the Abstract Syntax Tree to extract code structure.
        
        Args:
            tree (ast.AST): The AST to analyze.
        
        Returns:
            CodeStructure: Extracted code structure.
        """
        structure = CodeStructure()
        current_class_stack = []

        # Create a set to track unique imports
        unique_imports = set()

        for node in ast.iter_child_nodes(tree):
            # Analyze imports with more precise filtering
            if isinstance(node, ast.Import):
                for alias in node.names:
                    unique_imports.add(alias.name)
        
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    for alias in node.names:
                        # For typing imports, only add Dict and List
                        if node.module == 'typing':
                            if alias.name in ['Dict', 'List']:
                                unique_imports.add(f'typing.{alias.name}')
                        # For collections, add the full import name
                        elif node.module == 'collections':
                            unique_imports.add(f'collections.{alias.name}')
                        # For other imports, add the module name
                        else:
                            unique_imports.add(node.module)

            # Analyze global variables
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        structure.variables.append(target.id)

            # Analyze classes
            elif isinstance(node, ast.ClassDef):
                # Process the class and its nested elements
                class_info = self._process_class(node)
                structure.classes.append(class_info)

            # Analyze top-level functions
            elif isinstance(node, ast.FunctionDef):
                function_info = {
                    'name': node.name,
                    'line': node.lineno,
                    'docstring': ast.get_docstring(node) or '',
                    'args': [
                        {
                            'name': arg.arg, 
                            'annotation': self._get_annotation(arg)
                        } for arg in node.args.args
                    ],
                    'returns': self._get_annotation(node)
                }
                structure.functions.append(function_info)

        # Convert unique imports to a list
        structure.imports = list(unique_imports)
        return structure

    def _process_class(self, node):
        """
        Process a class node and its nested elements.
        
        Args:
            node (ast.ClassDef): The class node to process.
        
        Returns:
            dict: Processed class information.
        """
        class_info = {
            'name': node.name,
            'line': node.lineno,
            'docstring': ast.get_docstring(node) or '',
            'methods': []
        }

        # Analyze methods and nested classes within the class
        for class_node in node.body:
            if isinstance(class_node, ast.FunctionDef):
                method_info = {
                    'name': class_node.name,
                    'line': class_node.lineno,
                    'docstring': ast.get_docstring(class_node) or '',
                    'args': [
                        {
                            'name': arg.arg, 
                            'annotation': self._get_annotation(arg)
                        } for arg in class_node.args.args if arg.arg != 'self'
                    ]
                }
                class_info['methods'].append(method_info)
            
            # Check for nested classes
            elif isinstance(class_node, ast.ClassDef):
                nested_class_info = self._process_class(class_node)
                class_info['methods'].append(nested_class_info)

        return class_info
