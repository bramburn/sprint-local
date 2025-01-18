from typing import ClassVar, Optional, Type
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

class BaseCustomTool(BaseTool):
    """
    Base class for custom LangChain file management tools.
    
    Provides a common structure for file-related tools with input validation
    and error handling.
    """
    name: ClassVar[str]
    description: ClassVar[str]
    args_schema: ClassVar[Optional[Type[BaseModel]]] = None

    def _run(self, *args, **kwargs):
        """
        Implement the core functionality of the tool.
        
        Subclasses must override this method to provide specific file management logic.
        
        Args:
            *args: Positional arguments for the tool.
            **kwargs: Keyword arguments for the tool.
        
        Returns:
            str: A message describing the result of the operation.
        
        Raises:
            NotImplementedError: If the method is not implemented by a subclass.
        """
        raise NotImplementedError("Subclasses must implement this method")

    async def _arun(self, *args, **kwargs):
        """
        Async version of _run method.
        
        Provides an asynchronous implementation for file management tools.
        
        Args:
            *args: Positional arguments for the tool.
            **kwargs: Keyword arguments for the tool.
        
        Returns:
            str: A message describing the result of the operation.
        
        Raises:
            NotImplementedError: If the method is not implemented by a subclass.
        """
        raise NotImplementedError("Subclasses must implement this method")
