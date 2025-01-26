import unittest
import json
import datetime
import shutil
from pathlib import Path
from vector_store_manager import VectorStoreManager

class TestVectorStoreManager(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for testing
        self.test_dir = Path("test_vector_store")
        self.test_dir.mkdir(exist_ok=True)
        self.manager = VectorStoreManager(str(self.test_dir))
        
    def tearDown(self):
        # Clean up test directory
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
            
    def test_load_metadata_empty(self):
        """Test loading metadata when no file exists."""
        metadata = self.manager.load_metadata()
        self.assertEqual(metadata["last_update"], None)
        self.assertEqual(metadata["files"], {})
        
    def test_save_and_load_metadata(self):
        """Test saving and loading metadata."""
        test_metadata = {
            "last_update": "2024-01-25T12:00:00",
            "files": {
                "file1.txt": "2024-01-25T10:00:00",
                "file2.txt": "2024-01-25T11:00:00"
            }
        }
        
        # Save metadata
        self.manager.save_metadata(test_metadata)
        
        # Load metadata and verify
        loaded_metadata = self.manager.load_metadata()
        self.assertEqual(loaded_metadata, test_metadata)
        
    def test_get_changed_files(self):
        """Test detecting changed files."""
        # Create initial metadata
        initial_time = datetime.datetime(2024, 1, 25, 10, 0)
        later_time = datetime.datetime(2024, 1, 25, 11, 0)
        
        initial_files = {
            "file1.txt": initial_time,
            "file2.txt": initial_time
        }
        
        self.manager.update_metadata(initial_files)
        
        # Test with modified file
        current_files = {
            "file1.txt": initial_time,  # Unchanged
            "file2.txt": later_time,    # Modified
            "file3.txt": later_time     # New file
        }
        
        changed_files = self.manager.get_changed_files(current_files)
        
        # Verify changes
        self.assertEqual(len(changed_files), 2)
        self.assertIn("file2.txt", changed_files)
        self.assertIn("file3.txt", changed_files)
        self.assertNotIn("file1.txt", changed_files)
        
    def test_update_metadata(self):
        """Test updating metadata with new file information."""
        current_time = datetime.datetime.now()
        files_with_dates = {
            "file1.txt": current_time,
            "file2.txt": current_time
        }
        
        self.manager.update_metadata(files_with_dates)
        
        # Load and verify metadata
        metadata = self.manager.load_metadata()
        self.assertIsNotNone(metadata["last_update"])
        self.assertEqual(len(metadata["files"]), 2)
        self.assertIn("file1.txt", metadata["files"])
        self.assertIn("file2.txt", metadata["files"])

if __name__ == '__main__':
    unittest.main() 