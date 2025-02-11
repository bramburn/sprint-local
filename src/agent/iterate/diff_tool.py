"""
Diff tool implementation for applying and generating diffs using the Myers' Diff Algorithm.
Provides a clean interface for the iterate agent to modify files.
"""
from typing import List, Optional, Dict, Any
from pathlib import Path
from dataclasses import dataclass
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from src.utils.diff.diff_patch import DiffPatch
from src.utils.diff.apply_patch import PatchApplicator
from src.utils.diff.patch import Patch, PatchOperation
from src.utils.diff.patch_file import PatchFile
from src.llm.openrouter import get_openrouter


@dataclass
class DiffResult:
    """Result of a diff operation."""
    success: bool
    message: str
    modified_content: Optional[List[str]] = None
    error: Optional[str] = None


class DiffInput(BaseModel):
    """Input schema for diff operations."""
    file_path: str = Field(..., description="Path to the file to modify")
    original_content: List[str] = Field(..., description="Original content of the file as list of lines")
    target_content: List[str] = Field(..., description="Desired content of the file as list of lines")


class DiffTool(BaseTool):
    """Tool for applying diffs to files using Myers' Diff Algorithm."""
    name = "diff_tool"
    description = "Apply diffs to files using Myers' Diff Algorithm"
    args_schema = DiffInput

    def __init__(self):
        super().__init__()
        self.diff_patch = DiffPatch()

    def _create_patch(self, original: List[str], target: List[str]) -> PatchFile:
        """Create a patch from original and target content."""
        return self.diff_patch.create_patch(original, target)

    def _apply_patch(self, original: List[str], patch: PatchFile) -> List[str]:
        """Apply a patch to the original content."""
        applicator = PatchApplicator(original)
        return applicator.apply_patch_file(patch)

    def _validate_file(self, file_path: str) -> bool:
        """Validate that the file exists and is accessible."""
        path = Path(file_path)
        return path.exists() and path.is_file()

    def _read_file(self, file_path: str) -> List[str]:
        """Read file content as list of lines."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.readlines()

    def _write_file(self, file_path: str, content: List[str]) -> None:
        """Write content to file."""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(content)

    def _run(self, file_path: str, original_content: List[str], target_content: List[str]) -> Dict[str, Any]:
        """Run the diff tool on the given file."""
        try:
            if not self._validate_file(file_path):
                return DiffResult(
                    success=False,
                    message=f"File not found or not accessible: {file_path}",
                    error="FileNotFoundError"
                ).__dict__

            # Create and apply patch
            patch = self._create_patch(original_content, target_content)
            modified_content = self._apply_patch(original_content, patch)

            # Write changes
            self._write_file(file_path, modified_content)

            return DiffResult(
                success=True,
                message=f"Successfully applied diff to {file_path}",
                modified_content=modified_content
            ).__dict__

        except Exception as e:
            return DiffResult(
                success=False,
                message=f"Failed to apply diff: {str(e)}",
                error=type(e).__name__
            ).__dict__

    async def _arun(self, file_path: str, original_content: List[str], target_content: List[str]) -> Dict[str, Any]:
        """Async version of run."""
        return self._run(file_path, original_content, target_content)
