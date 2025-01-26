from langchain_file import LangchainFile
import os

from datetime import datetime


def main():

    path_to_vector_store = os.path.join(os.getcwd(), "../vector_store/current")
    timestamp = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
    
    output_path_with_timestamp = f"{timestamp}-backlog.txt"
    output_path = os.path.join(os.getcwd(), "../instructions", output_path_with_timestamp)
    langchain_file = LangchainFile(
        vector_store_location=path_to_vector_store, text_path=output_path
    )
    # load instructions/current_instruction.md
    with open("../instructions/current_instruction.md", "r") as file:
        current_instruction = file.read()
    
    response = langchain_file.run(
        current_instruction
    )
    print(response)


if __name__ == "__main__":
    main()
