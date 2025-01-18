from typing import Dict, Any, Optional

class DriverState:
    """
    Represents the state of the Driver Agent.
    
    Attributes:
        plan (Dict[str, Any]): The plan to be executed.
        generated_code (str): The code generated from the plan.
        test_results (Dict[str, Any]): Results from testing the generated code.
        memory (Dict[str, Any]): Memory for storing state and metadata.
    """
    def __init__(self, plan: Dict[str, Any], generated_code: str = "", test_results: Dict[str, Any] = None, memory: Dict[str, Any] = None):
        self.plan = plan
        self.generated_code = generated_code
        self.test_results = test_results or {}
        self.memory = memory or {}

    def __getitem__(self, key):
        if key == 'plan':
            return self.plan
        elif key == 'generated_code':
            return self.generated_code
        elif key == 'test_results':
            return self.test_results
        elif key == 'memory':
            return self.memory
        else:
            raise KeyError(key)

    def __setitem__(self, key, value):
        if key == 'plan':
            self.plan = value
        elif key == 'generated_code':
            self.generated_code = value
        elif key == 'test_results':
            self.test_results = value
        elif key == 'memory':
            self.memory = value
        else:
            raise KeyError(key)

    def get(self, key, default=None):
        if key == 'plan':
            return self.plan
        elif key == 'generated_code':
            return self.generated_code
        elif key == 'test_results':
            return self.test_results
        elif key == 'memory':
            return self.memory
        else:
            return default

    def update(self, updates: Dict[str, Any]) -> 'DriverState':
        for key, value in updates.items():
            self[key] = value
        return self

    def __iter__(self):
        return iter(['plan', 'generated_code', 'test_results', 'memory'])

    def __len__(self):
        return 4

    def __contains__(self, key):
        return key in ['plan', 'generated_code', 'test_results', 'memory']

    def items(self):
        return [('plan', self.plan), ('generated_code', self.generated_code), ('test_results', self.test_results), ('memory', self.memory)]

    def keys(self):
        return ['plan', 'generated_code', 'test_results', 'memory']

    def values(self):
        return [self.plan, self.generated_code, self.test_results, self.memory]

    @property
    def selected_plan(self):
        return self.plan

    @selected_plan.setter
    def selected_plan(self, value):
        self.plan = value
