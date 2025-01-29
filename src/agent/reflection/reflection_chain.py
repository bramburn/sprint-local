from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain.prompts import HumanMessagePromptTemplate
from langchain.prompts import SystemMessagePromptTemplate
from src.agent.reflection.file_analyser import FileAnalyser
from src.llm.openrouter import get_openrouter
from src.vector.load import load_vector_store
import os
from langchain.schema.runnable import RunnablePassthrough, RunnableParallel

class ReflectionChain:
    def __init__(self):
        # Initialize the LLM (e.g., OpenRouter)
        self.llm = get_openrouter(model="google/gemma-2-9b-it")

        # Step 1: Define the initial reflection prompt
        self.initial_reflection = ChatPromptTemplate.from_messages(
            [
                SystemMessagePromptTemplate.from_template(
                    "You are an experienced programmer analyzing a coding problem."
                ),
                HumanMessagePromptTemplate.from_template(
                    self._get_backlog_template()
                ),
            ]
        )

        # Step 2: Define the complexity elaboration prompt
        self.complexity_elaboration = ChatPromptTemplate.from_messages(
            [
                SystemMessagePromptTemplate.from_template(
                    "You are an expert in algorithmic complexity analysis."
                ),
                HumanMessagePromptTemplate.from_template(
                    self._get_backlog_step_two_template()
                ),
            ]
        )

        # Create separate chains for each step
        self.initial_reflection_chain = (
            self.initial_reflection
            | self.llm
            | StrOutputParser()
        )

        self.complexity_elaboration_chain = (
            self.complexity_elaboration
            | self.llm
            | StrOutputParser()
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

    def _get_context_from_vector_store(self, query: str) -> tuple[str, str]:
        """Retrieve relevant context using vector search"""
        try:
            # Perform similarity search
            docs = self.vector_store.similarity_search(query, k=5)
            
            # Get unique file paths from metadata, handling missing 'full_path'
            unique_paths = list({doc.metadata.get("full_path", "") for doc in docs if "full_path" in doc.metadata})
            
            # Read full file contents and format them for context
            context = []
            for path in unique_paths:
                if path and os.path.exists(path):
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
            return "", ""

    def reflect(self, requirements: str, vector_store_path: str) -> str:
        """
        Generate a reflection for a given coding problem, including basic analysis and detailed complexity elaboration.
        Returns a dictionary with both the initial reflection and complexity elaboration outputs.
        """
        self.vector_store = load_vector_store(vector_store_path)  # Load FAISS vector store
        file_content, analysis = self._get_context_from_vector_store(requirements)
        
        # Prepare input for the initial reflection chain
        input_data = {
            "requirements": requirements,
            "file_content": file_content,
            "file_analysis": analysis,
        }

        # Execute the initial reflection chain
        initial_reflection_output = self.initial_reflection_chain.invoke(input_data)

        # Prepare input for the complexity elaboration chain
        complexity_input = {
            "initial_reflection": initial_reflection_output,
            "file_content": file_content,
            "file_analysis": analysis,
        }

        # Execute the complexity elaboration chain
        complexity_elaboration_output = self.complexity_elaboration_chain.invoke(complexity_input)
        # Return both outputs as a single string
        return f"Initial Reflection: {initial_reflection_output}\nComplexity Elaboration: {complexity_elaboration_output}"
