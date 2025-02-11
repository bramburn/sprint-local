# diff_patch.py

from typing import List, Tuple
from diff_match_patch import DiffMatchPatch
from patch import Patch, PatchOperation
from patch_file import PatchFile
from apply_patch import PatchApplicator


class DiffPatch:
    def __init__(self):
        self.dmp = DiffMatchPatch()

    def create_patch(self, a: List[str], b: List[str]) -> PatchFile:
        """
        Creates a patch file from two lists of strings.
        """
        diffs = self.dmp.myers_diff(a, b)
        patches = []
        current_patch = None

        line_a = 0
        line_b = 0

        for diff in diffs:
            op, a_line, b_line = diff
            if current_patch is None:
                current_patch = Patch(start_a=line_a, start_b=line_b)

            if op == "=":
                if current_patch.operations:
                    patches.append(current_patch)
                    current_patch = None
                line_a += 1
                line_b += 1
            elif op == "-":
                current_patch.operations.append(
                    PatchOperation(operation="-", content=a_line)
                )
                line_a += 1
            elif op == "+":
                current_patch.operations.append(
                    PatchOperation(operation="+", content=b_line)
                )
                line_b += 1

        if current_patch and current_patch.operations:
            patches.append(current_patch)

        return PatchFile(patches=patches)

    def apply_patch(self, original_text: List[str], patch_file: PatchFile) -> List[str]:
        """
        Applies the given patch file to the original text.
        """
        applicator = PatchApplicator(original_text)
        return applicator.apply_patch_file(patch_file)
