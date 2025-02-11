from typing import List, Dict, Any, Optional
from langchain.agents import AgentExecutor
from langchain.agents.format_scratchpad import format_to_openai_function_messages
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.tools import StructuredTool
from langchain_core.tools import Tool
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import BaseModel, Field
from src.llm.openrouter import get_openrouter
from src.vector.load import load_vector_store_by_name
from src.utils.file_utils import safe_read_file, file_exists
from src.agent.iterate.nested_schema import NestedInstruction
import os

class BacklogAnalysisOutput(BaseModel):
    """Output schema for the backlog analysis."""
    improved_backlog: str = Field(..., description="The improved backlog with atomic detail checklist")
    nested_instructions: List[NestedInstruction] = Field(..., description="List of nested instructions for each file")
    original_prompt: str = Field(..., description="Original user prompt for reference")
    relevant_files: List[str] = Field(..., description="List of files relevant to the task")

class BacklogAgent:
    def __init__(self, working_dir: str):
        """
        Initialize the BacklogAgent.
        
        Args:
            working_dir: Base directory path for resolving relative file paths
        """
        self.working_dir = os.path.abspath(working_dir)
        self.llm = get_openrouter()
        self.vector_store = load_vector_store_by_name("roo-code")
        
        # Define tools
        self.tools = [
            StructuredTool(
                name="check_file_exists",
                description="Check if a file exists in the codebase. Provide the file path relative to the working directory.",
                func=self._check_file_exists,
                args_schema=lambda: BaseModel.construct(
                    __fields__={"file_path": (str, Field(description="Relative path to the file from the working directory"))}
                ),
            ),
            StructuredTool(
                name="read_file",
                description="Read contents of a file. Provide the file path relative to the working directory.",
                func=self._read_file,
                args_schema=lambda: BaseModel.construct(
                    __fields__={"file_path": (str, Field(description="Relative path to the file from the working directory"))}
                ),
            ),
            StructuredTool(
                name="analyze_content",
                description="Analyze file content and provide insights. Provide the file path relative to the working directory.",
                func=self._analyze_content,
                args_schema=lambda: BaseModel.construct(
                    __fields__={
                        "file_path": (str, Field(description="Relative path to the file from the working directory")),
                    }
                ),
            ),
            StructuredTool(
                name="search_similar_code",
                description="Search for similar code snippets in the vector store",
                func=self._search_similar_code,
                args_schema=lambda: BaseModel.construct(
                    __fields__={"query": (str, Field(description="Query to search for similar code"))}
                ),
            ),
        ]

        # Create agent prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a code analysis agent that improves backlog instructions by analyzing code context.
            Your goal is to:
            1. Find and analyze relevant files
            2. Search for similar code patterns
            3. Improve the backlog with atomic detail and checklist
            4. Create nested instructions for each file that needs modification

            Always maintain traceability between the original request and your improvements."""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        # Create agent executor
        self.agent_executor = AgentExecutor(
            agent=self._create_agent(),
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
        )

    def _create_agent(self):
        def _format_tool_to_function(tool):
            return {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.args,
            }

        functions = [_format_tool_to_function(t) for t in self.tools]
        
        return (
            {
                "input": lambda x: x["input"],
                "chat_history": lambda x: x.get("chat_history", [])[-10:],  # Limit to last 10 messages
                "agent_scratchpad": lambda x: format_to_openai_function_messages(
                    x.get("intermediate_steps", [])
                ),
            }
            | self.prompt
            | self.llm.bind(functions=functions)
            | OpenAIFunctionsAgentOutputParser()
        )

    def _check_file_exists(self, file_path: str) -> bool:
        """Check if a file exists."""
        return file_exists(self.working_dir, file_path)

    def _read_file(self, file_path: str) -> str:
        """Read file contents."""
        return safe_read_file(self.working_dir, file_path)

    def _analyze_content(self, file_path: str) -> Dict[str, Any]:
        """Analyze file content using LLM."""
        content = safe_read_file(self.working_dir, file_path)
        
        # Load and format the analysis prompt template
        with open(os.path.join(os.path.dirname(__file__), 'prompts', 'analyse.md'), 'r') as f:
            prompt_template = f.read()
            
        prompt = ChatPromptTemplate.from_messages([
            ("system", prompt_template),
            ("human", {"code": content})
        ])
        
        response = self.llm(prompt.format_messages())
        return {
            "analysis": response.content,
            "file_path": file_path,
        }

    def _search_similar_code(self, query: str) -> List[Dict[str, Any]]:
        """Search for similar code snippets in vector store."""
        results = self.vector_store.similarity_search_with_score(query, k=5)
        return [
            {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "similarity": score,
                "full_path": os.path.join(self.working_dir, doc.metadata["source"]) if "source" in doc.metadata else None
            }
            for doc, score in results
        ]

    def improve_backlog(self, backlog_text: str, original_prompt: str) -> BacklogAnalysisOutput:
        """
        Improve the backlog by analyzing code context and creating detailed instructions.
        
        Args:
            backlog_text: The original backlog text to improve
            original_prompt: The original user prompt
            
        Returns:
            BacklogAnalysisOutput containing improved backlog and nested instructions
        """
        # Run the agent
        result = self.agent_executor.invoke({
            "input": f"""Analyze and improve this backlog instruction:
            
            Working Directory: {self.working_dir}
            
            Original Prompt: {original_prompt}
            
            Current Backlog:
            {backlog_text}
            
            Find relevant files within the working directory, analyze them, and create an improved backlog with atomic detail.
            
            Ensure all file paths are relative to the working directory: {self.working_dir}"""
        })

        # Parse the agent's response into structured output
        return BacklogAnalysisOutput(
            improved_backlog=result["output"],
            nested_instructions=result.get("nested_instructions", []),
            original_prompt=original_prompt,
            relevant_files=result.get("relevant_files", []),
        )

    def run(self, backlog_text: str, original_prompt: str) -> BacklogAnalysisOutput:
        return self.improve_backlog(backlog_text, original_prompt)