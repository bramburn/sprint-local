import json
from typing import Dict, List, Any
import re

class TypeScriptCodeAnalyzer:
    def __init__(self):
        pass

    def analyze_code(self, code: str, file_path: str) -> Dict[str, Any]:
        """
        Analyze TypeScript/JavaScript code and extract metadata.
        
        :param code: Source code string
        :param file_path: Path to the source file
        :return: Dictionary containing extracted metadata
        """
        return {
            'functions': self._extract_functions(code),
            'classes': self._extract_classes(code),
            'imports': self._extract_imports(code),
            'variables': self._extract_variables(code)
        }

    def _extract_functions(self, code: str) -> List[Dict[str, Any]]:
        """
        Extract function definitions from the code.
        
        :param code: Source code string
        :return: List of function metadata
        """
        function_pattern = re.compile(
            r'(async\s+)?(?:function\s+)?(\w+)\s*\((.*?)\)(?:\s*:\s*(\w+))?\s*{',
            re.DOTALL
        )
        docstring_pattern = re.compile(r'/\*\*(.*?)\*/', re.DOTALL)
        
        functions = []
        for match in function_pattern.finditer(code):
            is_async = bool(match.group(1))
            name = match.group(2)
            params_str = match.group(3)
            return_type = match.group(4) or 'void'
            
            # Find docstring
            docstring_match = docstring_pattern.search(code[:match.start()])
            docstring = docstring_match.group(1).strip() if docstring_match else ''
            
            # Parse parameters
            params = []
            if params_str.strip():
                for param in params_str.split(','):
                    param_parts = param.strip().split(':')
                    param_name = param_parts[0].strip()
                    param_type = param_parts[1].strip() if len(param_parts) > 1 else 'any'
                    params.append({
                        'name': param_name,
                        'type': param_type
                    })
            
            functions.append({
                'name': name,
                'is_async': is_async,
                'docstring': docstring,
                'args': params,
                'returns': return_type
            })
        
        return functions

    def _extract_classes(self, code: str) -> List[Dict[str, Any]]:
        """
        Extract class definitions from the code.
        
        :param code: Source code string
        :return: List of class metadata
        """
        class_pattern = re.compile(
            r'class\s+(\w+)(?:\s+extends\s+\w+)?\s*{(.*?)}',
            re.DOTALL
        )
        method_pattern = re.compile(
            r'(?:(\w+)\s*\((.*?)\)(?:\s*:\s*(\w+))?)\s*{',
            re.DOTALL
        )
        docstring_pattern = re.compile(r'/\*\*(.*?)\*/', re.DOTALL)
        
        classes = []
        for class_match in class_pattern.finditer(code):
            class_name = class_match.group(1)
            class_body = class_match.group(2)
            
            # Find class docstring
            docstring_match = docstring_pattern.search(code[:class_match.start()])
            class_docstring = docstring_match.group(1).strip() if docstring_match else ''
            
            # Extract methods
            methods = []
            for method_match in method_pattern.finditer(class_body):
                method_name = method_match.group(1)
                params_str = method_match.group(2)
                return_type = method_match.group(3) or 'void'
                
                # Parse parameters
                params = []
                if params_str.strip():
                    for param in params_str.split(','):
                        param_parts = param.strip().split(':')
                        param_name = param_parts[0].strip()
                        param_type = param_parts[1].strip() if len(param_parts) > 1 else 'any'
                        params.append({
                            'name': param_name,
                            'type': param_type
                        })
                
                methods.append({
                    'name': method_name,
                    'args': params,
                    'returns': return_type
                })
            
            classes.append({
                'name': class_name,
                'docstring': class_docstring,
                'methods': methods
            })
        
        return classes

    def _extract_imports(self, code: str) -> List[Dict[str, Any]]:
        """
        Extract import statements from the code.
        
        :param code: Source code string
        :return: List of import metadata
        """
        import_pattern = re.compile(
            r'import\s+(?:(\w+)\s*,\s*)?(?:{([^}]+)})?(?:\s*from)?\s*[\'"]([^\'\"]+)[\'"]',
            re.MULTILINE
        )
        
        imports = []
        for match in import_pattern.finditer(code):
            default_import = match.group(1)
            named_imports = [imp.strip() for imp in match.group(2).split(',') if imp.strip()] if match.group(2) else []
            module = match.group(3)
            
            imports.append({
                'module': module,
                'default_import': default_import,
                'named_imports': named_imports
            })
        
        return imports

    def _extract_variables(self, code: str) -> List[str]:
        """
        Extract variable declarations from the code.
        
        :param code: Source code string
        :return: List of variable names
        """
        var_pattern = re.compile(
            r'(?:const|let|var)\s+(\w+)(?:\s*:\s*\w+)?(?:\s*=)?',
            re.MULTILINE
        )
        
        return [match.group(1) for match in var_pattern.finditer(code)]
