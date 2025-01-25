from langchain_file import LangchainFile


def main():
    langchain_file = LangchainFile()
    response = langchain_file.run("merge the cli to search the vector using only of the files and avoid duplicate --search and --vsearch")
    print(response)

if __name__ == "__main__":
    main()
