from pydantic import BaseModel, Field
from typing import List


class DirectoryStructureInformation(BaseModel):
    framework: str = Field(
        description="Explanation of the directory structure's potential framework"
    )
    modules: List[str] = Field(
        description="List of potential different modules or components identified in the directory structure"
    )
    settings_file: str = Field(description="Path to potential settings file")
    configuration_file: str = Field(description="Path to potential configuration file")
    explanation: str = Field(
        description="Explanation of how you came to understand the directory structure"
    )
