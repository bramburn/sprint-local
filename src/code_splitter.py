from pathlib import Path
from typing import Dict, List, Optional, Tuple
import ast
import os

from analyzers.python_analyzer import PythonAnalyzer
from analyzers.base import CodeStructure

class CodeSplitter:
    """
    Splits Python source files into logical components while preserving functionality.
    
    Features:
    - Intelligent code splitting based on class and function dependencies
    - Vector operation preservation
    - Import statement management
    - Line number tracking
    """
    
    def __init__(self, max_file_size: int = 500):
        """
        Initialize the code splitter.
        
        Args:
            max_file_size: Maximum number of lines per file (default: 500)
        """
        self.max_file_size = max_file_size
        self.analyzer = PythonAnalyzer()
        
    def split_file(self, file_path: Path) -> List[Tuple[str, str]]:
        """
        Split a Python file into logical components.
        
        Args:
            file_path: Path to the Python file to split
            
        Returns:
            List of tuples containing (new_file_name, content)
        """
        # Read and analyze the source file
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
            
        structure = self.analyzer.analyze_code(source, str(file_path))
        
        # If file is small enough, return as is
        if len(source.splitlines()) <= self.max_file_size:
            return [(str(file_path), source)]
            
        # Extract original imports and code
        tree = ast.parse(source)
        import_visitor = ImportVisitor()
        import_visitor.visit(tree)
        self.original_imports = import_visitor.imports
        
        # Extract original code blocks
        code_visitor = CodeVisitor(source)
        code_visitor.visit(tree)
        self.original_code = code_visitor.code_blocks
            
        # Group related components
        components = self._group_components(structure)
        
        # Generate new files
        return self._generate_files(components, file_path)
    
    def _group_components(self, structure: CodeStructure) -> List[Dict]:
        """
        Group related code components based on dependencies.
        
        Args:
            structure: Analyzed code structure
            
        Returns:
            List of component groups
        """
        groups = []
        
        # Track processed methods to avoid duplicates
        processed_methods = set()
        
        # Group classes with their methods
        for class_info in structure.classes:
            # Add methods to processed set
            for method in class_info['methods']:
                processed_methods.add(method['name'])
                
            group = {
                'type': 'class',
                'name': class_info['name'],
                'content': class_info,
                'dependencies': self._extract_dependencies(class_info)
            }
            groups.append(group)
        
        # Group standalone functions (excluding processed methods)
        for func in structure.functions:
            if func['name'] not in processed_methods:
                group = {
                    'type': 'function',
                    'name': func['name'],
                    'content': func,
                    'dependencies': self._extract_dependencies(func)
                }
                groups.append(group)
            
        return groups
    
    def _extract_dependencies(self, component: Dict) -> List[str]:
        """
        Extract dependencies from a code component.
        
        Args:
            component: Code component (class or function)
            
        Returns:
            List of dependency names
        """
        deps = set()
        
        # Extract base class dependencies
        if 'bases' in component:
            deps.update(component['bases'])
            
        # Extract dependencies from methods
        if 'methods' in component:
            for method in component['methods']:
                deps.update(self._extract_method_deps(method))
                
        return list(deps)
    
    def _extract_method_deps(self, method: Dict) -> List[str]:
        """
        Extract dependencies from a method.
        
        Args:
            method: Method information
            
        Returns:
            List of dependency names
        """
        deps = set()
        
        # Add decorator dependencies
        deps.update(method.get('decorators', []))
        
        return list(deps)
    
    def _generate_files(self, components: List[Dict], original_path: Path) -> List[Tuple[str, str]]:
        """
        Generate new files from component groups.
        
        Args:
            components: Grouped code components
            original_path: Path to the original file
            
        Returns:
            List of (file_name, content) tuples
        """
        files = []
        stem = original_path.stem
        
        # Generate imports file
        imports_content = self._generate_imports(components)
        files.append((f"{stem}_imports.py", imports_content))
        
        # Generate component files
        for group in components:
            content = self._generate_component_file(group, stem)
            name = f"{stem}_{group['name'].lower()}.py"
            files.append((name, content))
            
        return files
    
    def _generate_imports(self, components: List[Dict]) -> str:
        """Generate imports file content."""
        imports = []
        
        # Add original imports first
        imports.extend(self.original_imports)
        imports.append("")
        
        # Add typing imports if not already present
        if not any("typing" in imp for imp in self.original_imports):
            imports.insert(0, "from typing import List, Dict, Optional, Any")
            imports.insert(1, "")
        
        # Add component imports
        for comp in components:
            name = comp['name']
            imports.append(f"from .{name.lower()} import {name}")
            
        return "\n".join(imports)
    
    def _generate_component_file(self, component: Dict, module_stem: str) -> str:
        """Generate content for a component file."""
        lines = [
            f"# Generated component file for {component['name']}",
            f"from .{module_stem}_imports import *",
            "",
            ""
        ]
        
        # Add component code
        if component['type'] == 'class':
            # Try to find original code block
            original_code = self.original_code.get(component['name'])
            if original_code:
                lines.extend(original_code.split('\n'))
            else:
                lines.extend(self._format_class(component['content']))
        else:
            original_code = self.original_code.get(component['name'])
            if original_code:
                lines.extend(original_code.split('\n'))
            else:
                lines.extend(self._format_function(component['content']))
            
        return "\n".join(lines)
    
    def _format_class(self, class_info: Dict) -> List[str]:
        """Format a class definition."""
        lines = []
        
        # Add class definition
        bases = ", ".join(class_info['bases']) if class_info['bases'] else ""
        class_def = f"class {class_info['name']}"
        if bases:
            class_def += f"({bases})"
        lines.append(class_def + ":")
        
        # Add methods
        for method in class_info['methods']:
            method_lines = self._format_function(method)
            lines.extend("    " + line for line in method_lines)
            
        if not class_info['methods']:
            lines.append("    pass")
            
        return lines
    
    def _format_function(self, func_info: Dict) -> List[str]:
        """Format a function definition."""
        lines = []
        
        # Add decorators
        for decorator in func_info.get('decorators', []):
            lines.append(f"@{decorator}")
            
        # Add function definition
        args = ", ".join(func_info['args'])
        lines.append(f"def {func_info['name']}({args}):")
        lines.append("    pass  # TODO: Implement function body")
        
        return lines

class ImportVisitor(ast.NodeVisitor):
    """AST visitor to extract import statements."""
    
    def __init__(self):
        self.imports = []
        
    def visit_Import(self, node: ast.Import):
        """Extract import statements."""
        for alias in node.names:
            if alias.asname:
                self.imports.append(f"import {alias.name} as {alias.asname}")
            else:
                self.imports.append(f"import {alias.name}")
        
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Extract from-import statements."""
        if node.module:
            names = []
            for alias in node.names:
                if alias.asname:
                    names.append(f"{alias.name} as {alias.asname}")
                else:
                    names.append(alias.name)
            self.imports.append(f"from {node.module} import {', '.join(names)}")

class NodeVisitor(ast.NodeVisitor):
    """Base visitor that tracks parent nodes."""
    
    def visit(self, node):
        """Visit a node and set its parent."""
        if hasattr(node, 'parent'):
            return super().visit(node)
            
        parent = getattr(self, '_parent', None)
        node.parent = parent
        
        old_parent = parent
        self._parent = node
        super().visit(node)
        self._parent = old_parent
        
        return node

class CodeVisitor(NodeVisitor):
    """AST visitor to extract original code blocks."""
    
    def __init__(self, source_code: str):
        self.code_blocks = {}
        self.source_lines = source_code.split('\n')
        self._parent = None
        
    def get_source_segment(self, node: ast.AST) -> str:
        """Get source code segment for a node."""
        if not hasattr(node, 'lineno') or not hasattr(node, 'end_lineno'):
            return ""
        
        start = node.lineno - 1  # Convert to 0-based index
        end = node.end_lineno  # end_lineno is already the correct line
        
        # Extract the lines and preserve indentation
        lines = self.source_lines[start:end]
        return '\n'.join(lines)
        
    def visit_ClassDef(self, node: ast.ClassDef):
        """Extract class definitions with their methods."""
        source = self.get_source_segment(node)
        if source:
            self.code_blocks[node.name] = source
        self.generic_visit(node)
        
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Extract function definitions."""
        # Only store standalone functions
        if not isinstance(getattr(node, 'parent', None), ast.ClassDef):
            source = self.get_source_segment(node)
            if source:
                self.code_blocks[node.name] = source 