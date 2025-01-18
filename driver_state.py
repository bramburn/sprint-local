from typing import Dict, Any

class DriverState:
    def __init__(self):
        self._data = {
            'selected_plan': None,
            'generated_code': None,
            'test_results': [],
            'refined_code': None,
            'metadata': {}
        }

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value

    def get(self, key, default=None):
        return self._data.get(key, default)

    def update(self, updates: Dict[str, Any]) -> 'DriverState':
        self._data.update(updates)
        return self

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def __contains__(self, key):
        return key in self._data

    def items(self):
        return self._data.items()

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()
