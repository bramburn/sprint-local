# apply_patch.py

from typing import List
from patch_file import PatchFile
from patch import Patch, PatchOperation


class PatchApplicator:
    def __init__(self, original_text: List[str]):
        self.original_text = original_text.copy()
        self.patched_text = original_text.copy()

    def apply_patch_file(self, patch_file: PatchFile) -> List[str]:
        """
        Applies the given patch file to the original text.
        """
        offset_a = 0  # Tracks changes in original_text
        offset_b = 0  # Tracks changes in patched_text

        for patch in patch_file.patches:
            idx_a = patch.start_a + offset_a
            idx_b = patch.start_b + offset_b

            for op in patch.operations:
                if op.operation == "=":
                    # No change, move to next line
                    idx_a += 1
                    idx_b += 1
                elif op.operation == "-":
                    # Deletion from original_text
                    if 0 <= idx_b < len(self.patched_text):
                        del self.patched_text[idx_b]
                        offset_a -= 1
                elif op.operation == "+":
                    # Insertion to patched_text
                    if op.content is not None:
                        self.patched_text.insert(idx_b, op.content)
                        idx_b += 1
                        offset_b += 1
        return self.patched_text

    def get_patched_text(self) -> List[str]:
        return self.patched_text
