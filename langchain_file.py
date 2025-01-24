from llm_wrapper import LLMWrapper
from tools.file_editor import FileEditorTool, FileEditorInput
from tools.file_creator import FileCreatorTool
from langchain.prompts import PromptTemplate
import os
from config import config


class LangchainFile:
    def __init__(
        self,
        text_path="conversation.txt",
    ):
        self.llm_wrapper = LLMWrapper(
            provider="openrouter",
            api_key=config.OPENROUTER_API_KEY,
            model_name="meta-llama/llama-3.2-3b-instruct",
        )
        self.text_path = text_path

        self.file_editor = FileEditorTool()
        self.file_creator = FileCreatorTool()
        self._ensure_file_exists(self.text_path)
        self._ensure_file_exists(
            self.template_path, "This is a sample prompt template: {prompt}"
        )

    def _ensure_file_exists(self, file_path, default_content=""):
        """
        Ensure the file exists, creating it with default content if it doesn't.

        :param file_path: Path to the file
        :param default_content: Default content to write if the file is created
        """
        if not os.path.exists(file_path):
            self.file_creator._run(file_path, default_content)

    def _load_system_architecture_template(self):
        code = ""
        template_prompt = ""

        return PromptTemplate.from_template(template_prompt)

    def _load_epic_template(self):
        with open(
            os.path.join(os.path.dirname(__file__), "templates", "epic.md"), "r"
        ) as f:
            template_prompt = f.read()
        return PromptTemplate.from_template(template_prompt)

    def _load_template(self):
        """
        Load the prompt template from the specified file.

        :return: PromptTemplate object
        """
        with open(self.template_path, "r") as f:
            template_content = f.read()
        return PromptTemplate.from_template(template_content)

    def edit_template(self, new_content: str):
        """
        Edit the prompt template with new content.

        :param new_content: New content for the template
        """
        self.file_editor._run(
            FileEditorInput(file_path=self.template_path, new_content=new_content)
        )

    def run(self, prompt):
        """
        Execute the LLM interaction with the given prompt.

        :param prompt: User prompt
        :return: Response message
        """
        prompt_template = self._load_epic_template()
        formatted_prompt = prompt_template.format(user_requirement=prompt)
        llm_response = self.llm_wrapper.generate_response(formatted_prompt, {})

        if llm_response:
            with open(self.text_path, "a") as f:
                f.write(f"\nUser: {prompt}\nLLM: {llm_response}\n")

            second_prompt = f"{formatted_prompt}\n{llm_response}"
            second_llm_response = self.llm_wrapper.generate_response(second_prompt, {})

            if second_llm_response:
                with open(self.text_path, "a") as f:
                    f.write(f"\nLLM (second response): {second_llm_response}\n")
                return f"Responses saved to {self.text_path}"
            else:
                return f"First response saved to {self.text_path}, but second response failed."
        else:
            return "LLM response failed."
