from typing import List
from pydantic import BaseModel, Field

class NestedInstruction(BaseModel):
    instruction: str = Field(description="Instruction to be parsed")
    file_path: str = Field(description="Path to the file being modified")
    sub_instructions: List[str] = Field(
        default_factory=list, description="List of sub-instructions such as add, analyse, insert, update edit, or delete code for the given file"
    )