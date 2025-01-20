import unittest
from driver_nodes import analyze_plan, generate_code_node, static_analysis_node, fix_code_node, parse_code_structure
from models import PlanInfo, DriverState, TestResult, CodeStructure

class TestDriverNodes(unittest.TestCase):
    def setUp(self):
        self.test_plan = {
            "description": "implement function add_numbers with parameters x, y",
            "complexity": "low"
        }
        self.initial_state = DriverState(
            plan=self.test_plan,
            generated_code=None,
            code_structure=None,
            test_results=[],
            memory={},
            metadata={},
            next_node=None
        )

    def test_analyze_plan(self):
        """Test plan analysis with structured output"""
        result = analyze_plan(self.test_plan['description'])
        self.assertIsInstance(result, PlanInfo)
        self.assertEqual(result.function_name, "add_numbers")
        self.assertEqual(result.parameters, ["x", "y"])
        self.assertEqual(result.description, self.test_plan['description'])

    def test_parse_code_structure(self):
        """Test code structure parsing"""
        test_code = """
def add_numbers(x, y):
    '''Add two numbers'''
    return x + y

class Calculator:
    def multiply(self, a, b):
        return a * b
"""
        result = parse_code_structure(test_code)
        self.assertIsInstance(result, CodeStructure)
        self.assertEqual(len(result.functions), 1)
        self.assertEqual(result.functions[0]['name'], 'add_numbers')
        self.assertEqual(len(result.classes), 1)
        self.assertEqual(result.classes[0]['name'], 'Calculator')

    def test_generate_code_node(self):
        """Test code generation with structured output"""
        result = generate_code_node(self.initial_state.model_dump())
        self.assertIsInstance(result, DriverState)
        self.assertIsNotNone(result.generated_code)
        self.assertIn("def add_numbers(x, y):", result.generated_code)
        self.assertIsInstance(result.code_structure, CodeStructure)
        self.assertEqual(result.next_node, "static_analysis")

    def test_static_analysis_node(self):
        """Test static analysis with structured output"""
        state_with_code = generate_code_node(self.initial_state.model_dump())
        result = static_analysis_node(state_with_code.model_dump())
        
        self.assertIsInstance(result, DriverState)
        self.assertTrue(len(result.test_results) > 0)
        
        analysis_result = next(
            (r for r in result.test_results if r.type == 'static_analysis'),
            None
        )
        self.assertIsNotNone(analysis_result)
        self.assertIsInstance(analysis_result, TestResult)
        self.assertIn(analysis_result.type, ['static_analysis'])
        self.assertIn('passed_tests', analysis_result.model_dump())
        self.assertEqual(result.next_node, "code_testing")

    def test_fix_code_node(self):
        """Test code fixing with structured output"""
        state_with_code = generate_code_node(self.initial_state.model_dump())
        state_with_analysis = static_analysis_node(state_with_code.model_dump())
        result = fix_code_node(state_with_analysis.model_dump())
        
        self.assertIsInstance(result, DriverState)
        self.assertIsNotNone(result.refined_code)
        self.assertIsInstance(result.code_structure, CodeStructure)
        self.assertEqual(result.next_node, "code_testing")
        
        refinement_result = next(
            (r for r in result.test_results if r.type == 'code_refinement'),
            None
        )
        self.assertIsNotNone(refinement_result)
        self.assertTrue(refinement_result.results.get('refinement_applied', False))

    def test_error_handling(self):
        """Test error handling in nodes"""
        # Test with invalid state
        invalid_state = {}
        result = generate_code_node(invalid_state)
        self.assertIsInstance(result, DriverState)
        self.assertIn('error', result.metadata)

    def test_code_structure_details(self):
        """Test detailed code structure parsing"""
        test_code = """
def add_numbers(x, y):
    '''Add two numbers'''
    return x + y

class Calculator:
    def multiply(self, a, b):
        return a * b
"""
        result = parse_code_structure(test_code)
        self.assertIsInstance(result, CodeStructure)
        
        # Verify function details
        self.assertEqual(len(result.functions), 1)
        func_details = result.functions[0]
        self.assertEqual(func_details['name'], 'add_numbers')
        self.assertEqual(func_details['parameters'], ['x', 'y'])
        self.assertIn('docstring', func_details)
        
        # Verify class details
        self.assertEqual(len(result.classes), 1)
        class_details = result.classes[0]
        self.assertEqual(class_details['name'], 'Calculator')
        self.assertEqual(len(class_details['methods']), 1)
        self.assertEqual(class_details['methods'][0]['name'], 'multiply')

if __name__ == '__main__':
    unittest.main()