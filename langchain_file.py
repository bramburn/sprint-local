import os
from typing import List, Optional

from pydantic import BaseModel, Field

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from langchain_community.vectorstores import FAISS
import os
from config import config
from scanner import RepoScanner
from pathlib import Path


class EpicStructuredOutput(BaseModel):
    user_story: str = Field(..., description="User story for the task")
    affected_files: List[str] = Field(
        ..., description="List of files affected by the task"
    )
    description: str = Field(
        ..., description="Detailed description of the task or response"
    )
    acceptance_criteria: List[str] = Field(
        ..., description="List of acceptance criteria for the task"
    )
    additional_notes: Optional[List[str]] = Field(
        None, description="Optional additional notes or considerations"
    )


class LangchainFile:
    def __init__(
        self,
        text_path="conversation.txt",
        vector_store_location="vector_store/code",
    ):
        # Initialize LLM with structured output support
        self.llm = ChatOpenAI(
            model="meta-llama/llama-3.2-3b-instruct",
            temperature=0.7,  # Slight increase for creativity
            api_key=config.OPENROUTER_API_KEY,
            openai_api_base="https://openrouter.ai/api/v1",
        )

        # File paths and tools
        self.text_path = text_path

        # Initialize vector store and scanner
        vector_store_location = os.path.join(
            os.path.dirname(__file__), vector_store_location
        )
        self.vector_store = self._load_vector_store(vector_store_location)
        self.scanner = RepoScanner(os.path.dirname(__file__))

    def _load_vector_store(self, vector_store_location: str) -> FAISS:
        """
        Load a vector store from the specified location.

        Args:
            vector_store_location (str): Path to the vector store to load

        Returns:
            FAISS: Loaded vector store instance
        """
        # Validate vector store location
        if not Path(vector_store_location).exists():
            raise FileNotFoundError(
                f"Vector store directory not found: {vector_store_location}"
            )

        # Initialize embeddings with config API key
        embeddings = OpenAIEmbeddings(
            api_key=config.openai_key, model=config.embedding_model
        )

        try:
            # Load the FAISS index with safety flag
            vector_store = FAISS.load_local(
                vector_store_location, embeddings, allow_dangerous_deserialization=True
            )
            return vector_store
        except Exception as e:
            raise RuntimeError(f"Failed to load vector store: {str(e)}")

    def _search_vector_store(self, query: str, k: int = 10):
        """
        Perform a search on the loaded vector store.

        Args:
            query (str): Search query
            k (int): Number of results to return

        Returns:
            List[Dict[str, Any]]: Search results with metadata
        """
        results = self.vector_store.similarity_search_with_score(query, k=k)

        return [
            {
                "content": result.page_content,
                "score": score,
                "metadata": result.metadata,
                "file_path": result.metadata.get("file_path", "Unknown"),
            }
            for result, score in results
        ]

    def _get_structured_epic(self):
        from langchain.output_parsers import ResponseSchema, StructuredOutputParser

        epic_schema = ResponseSchema(
            name="epics",
            description="List of epics extracted from the content",
            type="list",  # Specify this is a list
            # Define the nested structure for each epic
            nested=[
                ResponseSchema(
                    name="user_story", description="User story for the task"
                ),
                ResponseSchema(
                    name="affected_files",
                    description="List of files affected by the task",
                    type="list",
                ),
                ResponseSchema(
                    name="description",
                    description="Detailed description of the task or response",
                ),
                ResponseSchema(
                    name="acceptance_criteria",
                    description="List of acceptance criteria for the task",
                    type="list",
                ),
                ResponseSchema(
                    name="additional_notes",
                    description="Optional additional notes or considerations",
                ),
            ],
        )
        parser = StructuredOutputParser.from_response_schemas([epic_schema])
        format_instructions = parser.get_format_instructions()
        prompt = PromptTemplate(
            template="""Split the following content into 1-5   epics in a structured output format. 
            Each epic should contain a user story, affected files, description, acceptance criteria, and additional notes.
            \n{format_instructions}\n{query}""",
            input_variables=["query"],
            partial_variables={"format_instructions": format_instructions},
        )

        return prompt, parser

    def _ensure_file_exists(self, file_path, default_content=""):
        """
        Ensure the file exists, creating it with default content if it doesn't.
        """
        if not os.path.exists(file_path):
            self.file_creator._run(file_path, default_content)

    def _get_file_content(self, file_paths):
        """
        Retrieve content for given file paths.

        Args:
            file_paths (List[str]): List of file paths to retrieve content from

        Returns:
            List[str]: List of file contents
        """
        content_list = []
        for file_path in file_paths:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content_list.append(f.read())
            except Exception as e:
                print(f"Error reading file {file_path}: {e}")
        return content_list

    def _load_epic_template(self):
        """
        Load the epic template from the templates directory.

        Returns:
            PromptTemplate: Loaded prompt template
        """
        with open(
            os.path.join(os.path.dirname(__file__), "templates", "epic.md"), "r"
        ) as f:
            template_prompt = f.read()
        return PromptTemplate.from_template(template_prompt)

    def _load_backlog_template(self):
        """
        Load the backlog template from the templates directory.

        Returns:
            PromptTemplate: Loaded backlog template
        """
        with open(
            os.path.join(os.path.dirname(__file__), "templates", "backlog.md"), "r"
        ) as f:
            template_prompt = f.read()
        return PromptTemplate.from_template(template_prompt)
      
    def _write_line(self, line):
        with open(self.text_path, "a") as f:
            f.write(line)

    def run(self, prompt):
        """
        Execute the LLM interaction with the given prompt.

        Args:
            prompt (str): User prompt

        Returns:
            str: Response message
        """
        # Query vector store for relevant files
        results = self._search_vector_store(prompt)
        file_paths = [result["file_path"] for result in results]

        # Load file content
        component_list = self._get_file_content(file_paths)

        # Format prompt with component list
        prompt_template = self._load_epic_template()
        formatted_prompt = prompt_template.format(
            user_requirement=prompt, component_list="\n\n".join(component_list)
        )

        # Prepare messages for ChatOpenAI
        messages = [
            SystemMessage(
                content="You are a helpful AI assistant specializing in software development. "
                "Provide clear, concise, and actionable responses in a structured format. "
                "Your response should include a description, acceptance criteria, and optional additional notes. "
                "Ensure the description is detailed, acceptance criteria are specific, "
                "and additional notes provide extra context or considerations."
            ),
            HumanMessage(content=formatted_prompt),
        ]

        # Call LLM with structured output
        epic_response = self.llm.invoke(messages)

        prompt, parser = self._get_structured_epic()
        chain = prompt | self.llm | parser
        if isinstance(epic_response, AIMessage):
          epic_response = epic_response.content
        else:
          epic_response = epic_response
        self._write_line(f"\nUser: {prompt}\nLLM: {epic_response}\n")
        structured_output = chain.invoke({"query": epic_response})

        if isinstance(structured_output, AIMessage):
            content = structured_output.content
        else:
            content = structured_output
        # check if we have more than one epic
        count = 1
        backlog = []

        # get backlog template
        backlog_template = self._load_backlog_template()

        if isinstance(content["epics"], list):
            for epic in content["epics"]:
                self._write_line(f"\n\n\nEpic {count}\n")

                backlog_prompt = f"Please create a detailed step-by-step instructions for Epic {count}. "

                # prepare acceptance criteria
                if "acceptanceCriteria" in epic:
                    if isinstance(epic["acceptanceCriteria"], list):
                        acceptance_criteria = "\n".join(epic["acceptanceCriteria"])
                    else:
                        acceptance_criteria = epic["acceptanceCriteria"]
                    backlog_prompt += f"Ensure to cover testing to achieve the acceptance criteria. \n\n Acceptance Criteria: \n{acceptance_criteria}"

                formatted_backlog = backlog_template.format(
                    epic_context=epic_response,
                    user_prompt=backlog_prompt,
                )
                content = self.llm.invoke(formatted_backlog)

                if isinstance(content, AIMessage):
                    content = content.content
                else:
                    content = content
                self._write_line(f"\nBacklog: {content}\n")
                count += 1
        self._write_line(f"\n\n\nFinished\n")

        return epic_response
