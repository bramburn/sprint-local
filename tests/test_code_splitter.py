import pytest
from pathlib import Path
from src.code_splitter import CodeSplitter

def test_code_splitter_init():
    """Test CodeSplitter initialization."""
    splitter = CodeSplitter()
    assert splitter.max_file_size == 500
    
    custom_splitter = CodeSplitter(max_file_size=1000)
    assert custom_splitter.max_file_size == 1000

def test_small_file_no_split(tmp_path):
    """Test that small files are not split."""
    # Create a small test file
    test_file = tmp_path / "small_test.py"
    content = """
def hello():
    print("Hello, World!")
    
class SimpleClass:
    def method(self):
        pass
"""
    test_file.write_text(content)
    
    splitter = CodeSplitter()
    result = splitter.split_file(test_file)
    
    assert len(result) == 1
    assert result[0][0] == str(test_file)
    assert result[0][1] == content

def test_large_file_split(tmp_path):
    """Test splitting a large file with multiple components."""
    # Create a large test file
    test_file = tmp_path / "large_test.py"
    content = "\n".join([
        "from typing import List, Dict",
        "",
        "class FirstClass:",
        "    def method1(self):",
        "        pass",
        "    def method2(self):",
        "        pass",
        "",
        "class SecondClass(FirstClass):",
        "    def method3(self):",
        "        pass",
        "",
        "def standalone_function():",
        "    pass",
    ] + ["# padding line" for _ in range(600)])  # Add padding to exceed max_file_size
    
    test_file.write_text(content)
    
    splitter = CodeSplitter()
    result = splitter.split_file(test_file)
    
    # Should generate imports file and component files
    assert len(result) == 4  # imports + 2 classes + 1 function
    
    # Check imports file
    imports_file = [r for r in result if r[0].endswith("_imports.py")][0]
    assert "from typing import List, Dict" in imports_file[1]
    assert "from .firstclass import FirstClass" in imports_file[1]
    assert "from .secondclass import SecondClass" in imports_file[1]
    
    # Check class files
    first_class = [r for r in result if "firstclass" in r[0].lower()][0]
    assert "class FirstClass:" in first_class[1]
    assert "def method1" in first_class[1]
    assert "def method2" in first_class[1]
    
    second_class = [r for r in result if "secondclass" in r[0].lower()][0]
    assert "class SecondClass(FirstClass):" in second_class[1]
    assert "def method3" in second_class[1]

def test_dependency_tracking():
    """Test that dependencies between components are correctly tracked."""
    content = """
class Base:
    def base_method(self):
        pass

class Child(Base):
    @property
    def prop(self):
        pass
"""
    
    splitter = CodeSplitter()
    structure = splitter.analyzer.analyze_code(content)
    components = splitter._group_components(structure)
    
    # Find Child class component
    child_component = next(c for c in components if c['name'] == 'Child')
    
    # Should have Base as dependency
    assert 'Base' in child_component['dependencies']
    # Should have property decorator dependency
    assert 'property' in child_component['dependencies']

def test_vector_operations_split(tmp_path):
    """Test splitting a file with vector operations."""
    test_file = tmp_path / "vector_ops.py"
    content = """
import numpy as np
from typing import List, Dict

class VectorProcessor:
    def __init__(self, data: np.ndarray):
        self.data = data
        
    def process(self) -> np.ndarray:
        # Vector operation
        return np.dot(self.data, self.data.T)
        
    def normalize(self) -> np.ndarray:
        # More vector operations
        return self.data / np.linalg.norm(self.data)

def compute_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
""" + "\n".join(["# padding"] * 600)

    test_file.write_text(content)
    
    splitter = CodeSplitter()
    result = splitter.split_file(test_file)
    
    # Should generate imports and component files
    assert len(result) == 3  # imports + class + function
    
    # Check imports
    imports_file = [r for r in result if r[0].endswith("_imports.py")][0]
    assert "import numpy as np" in imports_file[1]
    
    # Check vector class
    vector_class = [r for r in result if "vectorprocessor" in r[0].lower()][0]
    assert "class VectorProcessor:" in vector_class[1]
    assert "def __init__" in vector_class[1]
    assert "def process" in vector_class[1]
    assert "def normalize" in vector_class[1]

def test_complex_inheritance(tmp_path):
    """Test splitting files with complex inheritance structures."""
    test_file = tmp_path / "complex.py"
    content = """
from abc import ABC, abstractmethod
from typing import List, Dict, Generic, TypeVar

T = TypeVar('T')

class BaseProcessor(ABC):
    @abstractmethod
    def process(self) -> None:
        pass

class DataProcessor(BaseProcessor, Generic[T]):
    def __init__(self, data: T):
        self.data = data
    
    def process(self) -> None:
        self._preprocess()
        self._main_process()
        self._postprocess()
    
    def _preprocess(self) -> None:
        pass
    
    def _main_process(self) -> None:
        pass
    
    def _postprocess(self) -> None:
        pass

class SpecialProcessor(DataProcessor[List[int]]):
    def _main_process(self) -> None:
        self.data.sort()
""" + "\n".join(["# padding"] * 600)

    test_file.write_text(content)
    
    splitter = CodeSplitter()
    result = splitter.split_file(test_file)
    
    # Check number of files
    assert len(result) == 4  # imports + 3 classes
    
    # Check imports
    imports_file = [r for r in result if r[0].endswith("_imports.py")][0]
    assert "from abc import ABC, abstractmethod" in imports_file[1]
    assert "from typing import" in imports_file[1]
    
    # Check inheritance chain
    base = [r for r in result if "baseprocessor" in r[0].lower()][0]
    assert "class BaseProcessor(ABC):" in base[1]
    
    data = [r for r in result if "dataprocessor" in r[0].lower()][0]
    assert "class DataProcessor(BaseProcessor, Generic[T]):" in data[1]
    assert "def _preprocess" in data[1]
    assert "def _main_process" in data[1]
    assert "def _postprocess" in data[1]
    
    special = [r for r in result if "specialprocessor" in r[0].lower()][0]
    assert "class SpecialProcessor(DataProcessor[List[int]]):" in special[1]
    assert "def _main_process" in special[1] 