import unittest
import os
import shutil
from pathlib import Path
from documentation import load_documentation_file, add_docs

class TestDocumentationLoading(unittest.TestCase):
    def setUp(self):
        # Create test files directory
        self.test_dir = Path("test_files")
        self.test_dir.mkdir(exist_ok=True)
        
    def tearDown(self):
        # Clean up test files
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        
    def test_load_markdown_file(self):
        # Create a test markdown file
        file_path = self.test_dir / "test.md"
        content = "# Test Document\n\n## Section 1\nThis is a test section.\n\n## Section 2\nThis is another test section."
        file_path.write_text(content)
        
        # Test loading the file
        result = load_documentation_file(str(file_path))
        
        # Verify the result
        self.assertIn('chunks', result)
        self.assertIn('metadata', result)
        self.assertEqual(result['metadata']['file_type'], '.md')
        self.assertTrue(len(result['chunks']) > 0)
        
    def test_load_empty_file(self):
        # Create an empty file
        file_path = self.test_dir / "empty.txt"
        file_path.touch()
        
        # Test loading empty file
        with self.assertRaises(ValueError):
            load_documentation_file(str(file_path))
            
    def test_load_nonexistent_file(self):
        # Test loading non-existent file
        with self.assertRaises(FileNotFoundError):
            load_documentation_file("nonexistent.txt")
            
    def test_add_docs(self):
        # Create a test markdown file
        file_path = self.test_dir / "test_add.md"
        content = "# Test Document\n\n## Section 1\nThis is a test section.\n\n## Section 2\nThis is another test section."
        file_path.write_text(content)
        
        # Test adding docs to vector store
        test_vector_store_path = str(self.test_dir / "vector_store")
        add_docs(str(file_path), test_vector_store_path)
        
        # Verify vector store was created
        self.assertTrue(Path(test_vector_store_path).exists())

if __name__ == '__main__':
    unittest.main() 