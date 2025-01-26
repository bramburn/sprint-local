import unittest
import os

from initialize_vector_store import initialize_vector_store

class TestVectorStoreInitialization(unittest.TestCase):
    def test_empty_file(self):
        # Create a temporary empty file
        with open("./vector_store/temp.txt", "w") as f:
            pass
        # Check if the file is empty
        self.assertEqual(os.path.getsize("./vector_store/temp.txt"), 0)
        # Initialize the vector store
        initialize_vector_store("./vector_store/temp.txt")
        # Check if the vector store is initialized correctly
        self.assertTrue(os.path.exists("./vector_store/initializes.py"))

    def test_non_empty_file(self):
        # Create a temporary non-empty file
        with open("./vector_store/temp.txt", "w") as f:
            f.write("Hello, World!")
        # Check if the file is not empty
        self.assertEqual(os.path.getsize("./vector_store/temp.txt"), 13)
        # Initialize the vector store
        initialize_vector_store("./vector_store/temp.txt")
        # Check if the vector store is not initialized
        self.assertTrue(os.path.exists("./vector_store/temp.txt"))

if __name__ == "__main__":
    unittest.main() 