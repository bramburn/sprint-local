import pytest
import os
from src.vector.create import XMLVectorCreator
from src.vector.load import load_vector_store

@pytest.fixture
def sample_xml():
    return """<directory_structure>
file1.py
file2.py
</directory_structure>
<files>
<file path="file1.py">print("Hello")</file>
<file path="file2.py">def func(): pass</file>
</files>"""

def test_vector_creation(tmp_path, sample_xml):
    # Create test XML file
    xml_path = tmp_path / "test.xml"
    with open(xml_path, 'w') as f:
        f.write(sample_xml)
    
    # Create vector store
    output_dir = tmp_path / "vectors"
    creator = XMLVectorCreator()
    creator.create_vector_store(str(xml_path), str(output_dir))
    
    # Verify vector store was created
    assert os.path.exists(output_dir)
    assert os.path.exists(output_dir / "index.faiss")
    
    # Test loading
    vector_store = load_vector_store(str(output_dir))
    assert vector_store is not None 