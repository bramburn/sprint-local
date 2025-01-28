import asyncio
import resource
import signal
import sys
from typing import Dict, Any, Optional
import traceback

class ExecutionResult:
    """Represents the result of a code execution."""
    def __init__(
        self, 
        success: bool, 
        output: Optional[str] = None, 
        error: Optional[str] = None
    ):
        self.success = success
        self.output = output
        self.error = error

class SafeExecutionEnvironment:
    """Provides a secure environment for code execution with resource limits."""
    
    def __init__(
        self, 
        max_memory_mb: int = 512, 
        max_cpu_time: int = 30,
        max_processes: int = 1
    ):
        self.max_memory_mb = max_memory_mb
        self.max_cpu_time = max_cpu_time
        self.max_processes = max_processes
    
    def _set_resource_limits(self):
        """Set resource limits for the current process."""
        # Memory limit
        resource.setrlimit(
            resource.RLIMIT_AS, 
            (self.max_memory_mb * 1024 * 1024, self.max_memory_mb * 1024 * 1024)
        )
        
        # CPU time limit
        resource.setrlimit(
            resource.RLIMIT_CPU, 
            (self.max_cpu_time, self.max_cpu_time)
        )
        
        # Process limit
        resource.setrlimit(
            resource.RLIMIT_NPROC, 
            (self.max_processes, self.max_processes)
        )
    
    async def execute_safely(
        self, 
        code: str, 
        globals_dict: Optional[Dict[str, Any]] = None,
        locals_dict: Optional[Dict[str, Any]] = None
    ) -> ExecutionResult:
        """
        Execute code in a sandboxed environment with resource limits.
        
        Args:
            code (str): Python code to execute
            globals_dict (dict, optional): Global namespace
            locals_dict (dict, optional): Local namespace
        
        Returns:
            ExecutionResult: Execution outcome
        """
        # Default namespaces if not provided
        globals_dict = globals_dict or {}
        locals_dict = locals_dict or {}
        
        try:
            # Set resource limits
            self._set_resource_limits()
            
            # Compile code first to catch syntax errors
            compiled_code = compile(code, '<string>', 'exec')
            
            # Execute in a controlled environment
            exec(compiled_code, globals_dict, locals_dict)
            
            return ExecutionResult(success=True, output="Execution successful")
        
        except MemoryError:
            return ExecutionResult(
                success=False, 
                error="Memory limit exceeded"
            )
        
        except TimeoutError:
            return ExecutionResult(
                success=False, 
                error="Execution timed out"
            )
        
        except Exception as e:
            return ExecutionResult(
                success=False, 
                error=f"Execution failed: {str(e)}\n{traceback.format_exc()}"
            )
    
    @staticmethod
    def sanitize_input(code: str) -> str:
        """
        Basic input sanitization to prevent dangerous code execution.
        
        Args:
            code (str): Input code to sanitize
        
        Returns:
            str: Sanitized code
        """
        # Remove potential dangerous imports
        dangerous_imports = [
            'os', 'sys', 'subprocess', 'shutil', 'ctypes'
        ]
        
        for module in dangerous_imports:
            if f'import {module}' in code or f'from {module}' in code:
                raise ValueError(f"Importing {module} is not allowed")
        
        return code
