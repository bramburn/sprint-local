from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain.prompts import HumanMessagePromptTemplate
from src.agent.reflection.file_analyser import FileAnalyser
from src.llm.openrouter import get_openrouter
from src.vector.load import load_vector_store
import os
from langchain.schema.runnable import RunnablePassthrough

class ReflectionChain:
    def __init__(self):
        # Initialize the LLM (e.g., OpenRouter)
        self.llm = get_openrouter()

        # Step 1: Define the initial reflection prompt

        self.initial_reflection = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an experienced programmer analyzing a coding problem.",
                ),
                (
                    "user",
                    HumanMessagePromptTemplate.from_template(
                        self._get_backlog_template()
                    ),
                ),
            ]
        )

        # Step 2: Define the complexity elaboration prompt
        self.complexity_elaboration = ChatPromptTemplate.from_messages(
            [
                ("system", "You are an expert in algorithmic complexity analysis."),
                (
                    "user",
                    HumanMessagePromptTemplate.from_template(
                        self._get_backlog_step_two_template()
                    ),
                ),
            ]
        )

    def _get_backlog_template(self):
        with open(
            os.path.join(
                os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    "prompts",
                    "backlog.md",
                )
            ),
            "r",
        ) as f:
            content = f.read()
        return content

    def _get_backlog_step_two_template(self):
        with open(
            os.path.join(
                os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    "prompts",
                    "backlog_step_two.md",
                )
            ),
            "r",
        ) as f:
            content = f.read()
        return content

    def _get_context_from_vector_store(self, query: str) -> str:
        """Retrieve relevant context using vector search"""
        try:
            # Perform similarity search
            docs = self.vector_store.similarity_search(query, k=5)

            # Get unique file paths from metadata
            unique_paths = list({doc.metadata["full_path"] for doc in docs})

            # Read full file contents and format them for context
            context = []
            for path in unique_paths:
                if os.path.exists(path):
                    with open(path, "r") as f:
                        content = f.read()
                        context.append(f"File: {path}\nContent:\n{content}")

            analysis = []
            file_analyser = FileAnalyser()
            for file_content in context:
                analysis.append(file_analyser.analyse_file(file_content))

            return "\n\n".join(context), "\n\n".join(analysis)

        except Exception as e:
            print(f"Error retrieving context: {e}")
            return ""

    def reflect(self, requirements: str, vector_store_path: str) -> str:
        """
        Generate a reflection for a given coding problem, including basic analysis and detailed complexity elaboration.

        Args:
            requirements (str): The requirements of the coding problem.

        Returns:
            str: The generated reflection as a string.
        """

        self.vector_store = load_vector_store(
            vector_store_path
        )  # Load FAISS vector store

        file_content, analysis = self._get_context_from_vector_store(requirements)
        # Define the chain with two steps
        self.chain = (
            {
                "initial_reflection": self.initial_reflection  # Step 1: Basic reflection
                | self.llm  # Process with LLM
                | StrOutputParser(),
                "file_content": RunnablePassthrough(),
                "file_analysis": RunnablePassthrough(),
            }
            | self.complexity_elaboration  # Step 2: Elaborate on complexity
            | self.llm  # Process with LLM again for detailed analysis
            | StrOutputParser(),
        )

        input_data = {
            "requirements": requirements,
            "file_content": file_content,
            "file_analysis": analysis,
        }

        # Invoke the chain to generate both steps of reflection
        return self.chain.invoke(input_data)
