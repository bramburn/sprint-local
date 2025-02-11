# example_usage.py

from diff_patch import DiffPatch
from patch_file import PatchFile


def main():
    # Sample original and modified texts
    original_text = [
        "The quick brown fox",
        "jumps over the lazy dog",
        "Lorem ipsum dolor sit amet",
        "consectetur adipiscing elit",
        "Sed do eiusmod tempor",
        "incididunt ut labore et dolore",
        "magna aliqua.",
    ]

    modified_text = [
        "That quick brown fox",
        "jumped over a lazy dog",
        "Lorem ipsum dolor sit amet",
        "consectetur adipiscing elit",
        "Sed do eiusmod tempor incididunt",
        "ut labore et dolore magna aliqua.",
    ]

    dp = DiffPatch()

    # Create patch
    patch_file = dp.create_patch(original_text, modified_text)
    patch_filename = "sample_patch.json"
    patch_file.write_to_file(patch_filename)
    print(f"Patch created and saved to {patch_filename}")

    # Read patch
    loaded_patch = PatchFile.read_from_file(patch_filename)

    # Apply patch
    patched_text = dp.apply_patch(original_text, loaded_patch)
    print("Patched Text:")
    for line in patched_text:
        print(line)


if __name__ == "__main__":
    main()
