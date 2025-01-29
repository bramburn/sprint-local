from src.llm.openrouter import get_openrouter
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
import os
from langchain.prompts import ChatPromptTemplate
from langchain.prompts import PromptTemplate
from langchain.schema.output_parser import StrOutputParser

class FileAnalyser:

    def __init__(self):

        self.llm = get_openrouter()

        file_analyser_template_path = os.path.join(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "prompts", "file_analyser.md")
        )
        file_analyser_content = self._load_file_analyser(file_analyser_template_path)

        self.step_one_analyse_workflow = ChatPromptTemplate.from_messages(
            [
                SystemMessagePromptTemplate.from_template(
                    "You are an experienced programmer analyzing a coding problem."
                ),
                HumanMessagePromptTemplate.from_template(file_analyser_content),
            ]
        )

        self.step_two_analyse_mermaid_workflow = ChatPromptTemplate.from_messages(
            [
                SystemMessagePromptTemplate.from_template(
                    "You are an experienced programmer at analyzing workflow and ensure completeness."
                ),
                HumanMessagePromptTemplate.from_template(
                    """
            Analyse the following workflow and ensure it is complete and logical:

            {step_one_analyse_workflow}


            If not, provide a revised workflow:
            """,
                ),
            ]
        )

    def _load_file_analyser(self, file_path: str) -> str:
        """Load the file content as a string."""
        with open(file_path, "r") as file:
            content = file.read()
        return content

    def analyse_file(self, file_content: str) -> str:
        """Analyse the content of a file and return a summary"""

        self.chain = (
            self.step_one_analyse_workflow
            | self.llm
            | StrOutputParser()
            | self.step_two_analyse_mermaid_workflow
            | self.llm
            | StrOutputParser()
        )

        return self.chain.invoke({"file_content": file_content})
