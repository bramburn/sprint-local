from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class CodeStructure:
    """Data structure representing analyzed code components."""
    classes: List[Dict]
    functions: List[Dict]
    imports: List[str]
    variables: List[str]

class BaseAnalyzer(ABC):
    """Base interface for code analyzers."""
    
    @abstractmethod
    def analyze_code(self, code: str, file_path: Optional[str] = None) -> CodeStructure:
        """
        Analyze the given code and return its structure.
        
        Args:
            code: The source code to analyze
            file_path: Optional path to the source file
            
        Returns:
            CodeStructure containing the analyzed components
        """
        pass 