import unittest
from driver_nodes import analyze_plan, generate_code_node, static_analysis_node, test_code_node, fix_code_node
from models import PlanInfo, DriverState, TestResult

class TestDriverNodes(unittest.TestCase):
    def setUp(self):
        self.test_plan = "implement function add_numbers with parameters x, y"
        self.initial_state = DriverState(
            selected_plan=self.test_plan,
            generated_code=None,
            test_results=[],
            metadata={},
            next=None
        )

    def test_analyze_plan(self):
        """Test plan analysis with structured output"""
        result = analyze_plan(self.test_plan)
        self.assertIsInstance(result, PlanInfo)
        self.assertEqual(result.function_name, "add_numbers")
        self.assertEqual(result.parameters, ["x", "y"])
        self.assertEqual(result.description, self.test_plan)

    def test_generate_code_node(self):
        """Test code generation with structured output"""
        result = generate_code_node(self.initial_state.dict())
        self.assertIsInstance(result, DriverState)
        self.assertIsNotNone(result.generated_code)
        self.assertIn("def add_numbers(x, y):", result.generated_code)
        self.assertEqual(result.next, "static_analysis")

    def test_static_analysis_node(self):
        """Test static analysis with structured output"""
        state_with_code = generate_code_node(self.initial_state.dict())
        result = static_analysis_node(state_with_code.dict())
        
        self.assertIsInstance(result, DriverState)
        self.assertTrue(len(result.test_results) > 0)
        
        analysis_result = next(
            (r for r in result.test_results if r.type == 'static_analysis'),
            None
        )
        self.assertIsNotNone(analysis_result)
        self.assertIsInstance(analysis_result, TestResult)
        self.assertEqual(result.next, "test_code")

    def test_test_code_node(self):
        """Test code testing with structured output"""
        state_with_analysis = static_analysis_node(
            generate_code_node(self.initial_state.dict()).dict()
        )
        result = test_code_node(state_with_analysis.dict())
        
        self.assertIsInstance(result, DriverState)
        self.assertTrue(len(result.test_results) > 1)
        
        test_result = next(
            (r for r in result.test_results if r.type == 'unit_tests'),
            None
        )
        self.assertIsNotNone(test_result)
        self.assertIsInstance(test_result, TestResult)

    def test_fix_code_node(self):
        """Test code fixing with structured output"""
        state_with_tests = test_code_node(
            static_analysis_node(
                generate_code_node(self.initial_state.dict()).dict()
            ).dict()
        )
        result = fix_code_node(state_with_tests.dict())
        
        self.assertIsInstance(result, DriverState)
        self.assertIsNotNone(result.refined_code)
        self.assertEqual(result.next, "test_code")

    def test_error_handling(self):
        """Test error handling in nodes"""
        # Test with invalid state
        invalid_state = {}
        result = generate_code_node(invalid_state)
        self.assertIsInstance(result, DriverState)
        self.assertIn('error', result.metadata)

if __name__ == '__main__':
    unittest.main() 