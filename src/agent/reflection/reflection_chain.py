from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain.prompts import HumanMessagePromptTemplate
from langchain.prompts import SystemMessagePromptTemplate
from src.agent.reflection.file_analyser import FileAnalyser
from src.llm.openrouter import get_openrouter
from src.vector.load import load_vector_store
import os
from langchain.schema.runnable import RunnablePassthrough, RunnableParallel
import logging
from typing import List
from src.agent.reflection.choose_best_option import EpicChooser, EpicSelection
from langchain_core.output_parsers import PydanticOutputParser, OutputParserException
from pydantic import ValidationError

logger = logging.getLogger(__name__)

class ReflectionChain:
    """
    A reflection chain is a sequence of language models that are used to generate a reflection for a given coding problem.
    The chain consists of two steps: an initial reflection and complexity elaboration.
    """

    def __init__(self):
        # Initialize the LLM (e.g., OpenRouter)
        self.llm = get_openrouter(model="meta-llama/llama-3.2-11b-vision-instruct")

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
        """
        Retrieve relevant context using vector search.
        
        Parameters:
        query (str): The query to search for in the vector store
        
        Returns:
        tuple[str, str]: A tuple containing the full file contents and the analysis of the files.
        """
        try:
            # Perform similarity search
            docs = vector_store.similarity_search(query, k=5)
            
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
        
        Parameters:
        requirements (str): The description of the coding problem
        vector_store_path (str): The path to the vector store
        
        Returns:
        str: A dictionary with both the initial reflection and complexity elaboration outputs.
        """
        # Retrieve context from vector store
        file_content, analysis = self._get_context_from_vector_store(requirements)

        # Prepare input data for initial reflection
        input_data = {
            "requirements": requirements,
            "file_content": file_content,
            "file_analysis": analysis,
        }

        # Generate 5 initial reflections
        initial_reflections: List[str] = []
        for _ in range(3):
            initial_reflection_output = self.initial_reflection_chain.invoke(input_data)
            initial_reflections.append(initial_reflection_output)

        # Use EpicChooser to select the best initial reflection
        epic_chooser = EpicChooser()
        epic_selection: EpicSelection = epic_chooser.choose_best_epic(
            requirement=requirements, 
            epics=initial_reflections
        )

        # Log the rationale for the chosen reflection
        logging.info(f"Initial Reflection Selection Rationale: {epic_selection.rationale}")

        # Get the index of the chosen reflection
        chosen_reflection_index = initial_reflections.index(epic_selection.chosen_epic_id)
        chosen_reflection = initial_reflections[chosen_reflection_index]

        # Prepare input for the complexity elaboration chain
        complexity_input = {
            "initial_reflection": chosen_reflection,
            "file_content": file_content,
            "file_analysis": analysis,
        }

        # Generate 5 complexity elaboration outputs
        complexity_elaborations: List[str] = []
        for _ in range(3):
            complexity_elaboration_output = self.complexity_elaboration_chain.invoke(complexity_input)
            complexity_elaborations.append(complexity_elaboration_output)

        # Use EpicChooser to select the best complexity elaboration
        complexity_epic_selection: EpicSelection = epic_chooser.choose_best_epic(
            requirement=requirements, 
            epics=complexity_elaborations
        )

        # Log the rationale for the chosen complexity elaboration
        logging.info(f"Complexity Elaboration Selection Rationale: {complexity_epic_selection.rationale}")

        # Get the index of the chosen complexity elaboration
        chosen_complexity_index = complexity_elaborations.index(complexity_epic_selection.chosen_epic_id)
        chosen_complexity_elaboration = complexity_elaborations[chosen_complexity_index]

        # Return both outputs as a single string
        return f"Initial Reflection: {chosen_reflection}\nComplexity Elaboration: {chosen_complexity_elaboration}"
