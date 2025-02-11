# patch_file.py

import json
from typing import List
from patch import Patch


class PatchFile:
    def __init__(self, patches: List[Patch]):
        self.patches = patches

    def serialize(self) -> str:
        """
        Serializes the patch file to a JSON string.
        """
        return json.dumps([patch.to_dict() for patch in self.patches], indent=4)

    @staticmethod
    def deserialize(patch_str: str):
        """
        Deserializes the patch file from a JSON string.
        """
        data = json.loads(patch_str)
        patches = [Patch.from_dict(patch) for patch in data]
        return PatchFile(patches=patches)

    def write_to_file(self, filename: str):
        """
        Writes the serialized patch to a file.
        """
        with open(filename, "w", encoding="utf-8") as f:
            f.write(self.serialize())

    @staticmethod
    def read_from_file(filename: str):
        """
        Reads and deserializes the patch from a file.
        """
        with open(filename, "r", encoding="utf-8") as f:
            patch_str = f.read()
        return PatchFile.deserialize(patch_str)
