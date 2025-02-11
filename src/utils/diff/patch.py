# patch.py

from typing import List, Tuple, Optional
from dataclasses import dataclass, field


@dataclass
class PatchOperation:
    """
    Represents a single patch operation.
    """

    operation: str  # '=', '-', '+'
    content: Optional[str] = None


@dataclass
class Patch:
    """
    Represents a patch with start line numbers and operations.
    """

    start_a: int
    start_b: int
    operations: List[PatchOperation] = field(default_factory=list)

    def to_dict(self):
        """
        Serializes the patch to a dictionary.
        """
        return {
            "start_a": self.start_a,
            "start_b": self.start_b,
            "operations": [
                {"op": op.operation, "content": op.content} for op in self.operations
            ],
        }

    @staticmethod
    def from_dict(data):
        """
        Deserializes the patch from a dictionary.
        """
        operations = [
            PatchOperation(op["op"], op["content"]) for op in data["operations"]
        ]
        return Patch(
            start_a=data["start_a"], start_b=data["start_b"], operations=operations
        )
