from typing import List, Union
import os

def read_file_with_line_numbers(file_path: str) -> List[str]:
    """
    Read a file and return its contents with line numbers.

    Args:
        file_path (str): Path to the file to be read.

    Returns:
        List[str]: List of strings with line numbers prefixed.

    Raises:
        FileNotFoundError: If the file does not exist.
        PermissionError: If there are insufficient permissions to read the file.
        IOError: For other I/O related errors.
    """
    try:
        # Normalize the file path to handle different OS path separators
        normalized_path = os.path.normpath(file_path)
        
        # Check if file exists before attempting to read
        if not os.path.exists(normalized_path):
            raise FileNotFoundError(f"File not found: {normalized_path}")
        
        # Read file contents
        with open(normalized_path, 'r', encoding='utf-8') as file:
            # Use enumerate to add line numbers
            return [f"{line_num + 1}: {line.rstrip()}" 
                    for line_num, line in enumerate(file.readlines())]
    
    except PermissionError:
        raise PermissionError(f"Permission denied when trying to read: {normalized_path}")
    except IOError as e:
        raise IOError(f"Error reading file {normalized_path}: {str(e)}")
