from typing import List, Any


from dataclasses import dataclass


@dataclass
class Ell_Response:
    text: str
    text_only: str
    tool_calls: List[Any]
    tool_results: List[Any]
    structured: Any
