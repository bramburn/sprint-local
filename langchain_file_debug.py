from langchain_file import LangchainFile
import os

from datetime import datetime


def main():

    path_to_vector_store = "vector_store/current"
    timestamp = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
    
    output_path_with_timestamp = f"{timestamp}-backlog.txt"
    output_path = os.path.join(os.getcwd(), "instructions", output_path_with_timestamp)
    langchain_file = LangchainFile(
        vector_store_location=path_to_vector_store, text_path=output_path
    )
    response = langchain_file.run(
        "update the initialize_vectore_store.py to check if the vector store is empty and if it is empty then create a new vector store, if its not then we print out its created"
    )
    print(response)


if __name__ == "__main__":
    main()
