import os
import glob
from pathlib import Path

def generate_directory_structure(
    code_dir: str, 
    output_dir: str,
    include_patterns: list[str] = None,
    ignore_patterns: list[str] = None
) -> None:
    """
    Generates a markdown file listing all files in the specified directory.
    
    Args:
        code_dir (str): Path to the directory to scan
        output_dir (str): Path to save the output markdown file
        include_patterns (list[str]): List of glob patterns to include
        ignore_patterns (list[str]): List of glob patterns to ignore
    """
    try:
        # Validate input paths
        if not os.path.isdir(code_dir):
            raise ValueError(f"Invalid code directory: {code_dir}")
        if not os.path.isdir(output_dir):
            raise ValueError(f"Invalid output directory: {output_dir}")

        # Get all files using glob
        files = glob.glob(f"{code_dir}/**/*", recursive=True)
        files = [f for f in files if os.path.isfile(f)]

        # Apply include patterns if specified
        if include_patterns:
            included_files = set()
            for pattern in include_patterns:
                included_files.update(glob.glob(pattern, recursive=True))
            files = [f for f in files if f in included_files]

        # Apply ignore patterns if specified
        if ignore_patterns:
            for pattern in ignore_patterns:
                files = [f for f in files if not Path(f).match(pattern)]

        # Generate markdown content
        markdown_content = "<directory_structure>\n"
        markdown_content += "\n".join(files)
        markdown_content += "\n</directory_structure>"

        # Write to output file
        output_path = Path(output_dir) / "directory.md"
        with open(output_path, 'w') as f:
            f.write(markdown_content)

    except Exception as e:
        print(f"Error generating directory structure: {str(e)}")
        raise
