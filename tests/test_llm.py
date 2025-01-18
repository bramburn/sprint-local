import unittest
import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from llm_wrapper import LLMWrapper

class TestLLMIntegration(unittest.TestCase):
    def setUp(self):
        """
        Set up the LLM wrapper for testing.
        """
        self.llm_wrapper = LLMWrapper()
    
    def test_api_key_validation(self):
        """
        Test API key validation.
        """
        self.assertTrue(self.llm_wrapper.validate_api_key(), 
                        "API key validation failed. Check your configuration.")
    
    def test_basic_prompt_response(self):
        """
        Test basic prompt generation.
        """
        prompt_template = "What is the capital of {country}?"
        input_variables = {"country": "France"}
        
        response = self.llm_wrapper.generate_response(prompt_template, input_variables)
        
        # Basic assertions
        self.assertIsNotNone(response, "LLM response should not be None")
        self.assertTrue(len(response.strip()) > 0, "Response should not be empty")
        self.assertIn("Paris", response, "Response should contain the expected capital")
    
    def test_error_handling(self):
        """
        Test error handling with an invalid prompt.
        """
        # Test with an empty prompt
        response = self.llm_wrapper.generate_response("", {})
        self.assertIsNone(response, "Invalid prompt should return None")

if __name__ == '__main__':
    unittest.main()
