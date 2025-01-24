from llm_wrapper import LLMWrapper
from tools.file_editor import FileEditorTool, FileEditorInput
from tools.file_creator import FileCreatorTool
from langchain.prompts import PromptTemplate
import os

class LangchainFile:
    def __init__(self, base_url=None, api_key=None, model_name=None, text_path='conversation.txt', template_path='prompt_template.txt'):
        self.llm_wrapper = LLMWrapper(base_url=base_url, api_key=api_key, model_name=model_name)
        self.text_path = text_path
        self.template_path = template_path
        self.file_editor = FileEditorTool()
        self.file_creator = FileCreatorTool()
        self._ensure_file_exists(self.text_path)
        self._ensure_file_exists(self.template_path, "This is a sample prompt template: {prompt}")

    def _ensure_file_exists(self, file_path, default_content=""):
        """
        Ensure the file exists, creating it with default content if it doesn't.
        
        :param file_path: Path to the file
        :param default_content: Default content to write if the file is created
        """
        if not os.path.exists(file_path):
            self.file_creator._run(file_path, default_content)
    def _load_code_analyzer_template(self):
        code = ""
        template_prompt = """
## Purpose

You are an expert in code analysis, skilled in conducting both static and dynamic analysis of software repositories. Your task is to generate a comprehensive analysis template based on the provided code repository files.

Your goal is to:  
- Analyze the codebase for structure, dependencies, code quality, and potential issues.  
- Provide insights into the static aspects like code complexity, adherence to coding standards, and design patterns.  
- Offer dynamic analysis insights related to runtime behavior, performance, and interaction patterns.  
- Format the response output as specified, excluding any repeated instructions or purpose statements.

---

## Instructions

- **Analyze the user-provided repository files to understand**:  
  - The overall structure and purpose of the codebase.  
  - Dependencies between different modules or components.  
  - Code quality metrics, such as cyclomatic complexity, code duplication, and maintainability.  
  - Potential security vulnerabilities or coding errors.  
  - Performance bottlenecks or inefficiencies.

- **Construct a detailed analysis report that**:  
  - Outlines the static analysis results, focusing on code structure, quality, and potential issues.  
  - Provides dynamic analysis insights, explaining how the code behaves at runtime, including performance, memory usage, and interaction with external systems.  
  - Incorporates placeholders for the provided files: [[files]].

- **Output the response in the following structured format**:  
  - **Introduction**: Begin with a brief introduction to the analysis, explaining the scope and purpose of the analysis.  
  - **Static Analysis**:  
    - **Code Structure**: Analyze the overall organization of the codebase.  
    - **Code Complexity**: Assess cyclomatic complexity, code duplication, and maintainability.  
    - **Potential Issues**: Identify any security vulnerabilities, coding errors, or anti-patterns.  
  - **Dynamic Analysis**:  
    - **Runtime Behavior**: Describe how the code behaves at runtime.  
    - **Performance**: Highlight performance bottlenecks or inefficiencies.  
    - **Interactions**: Explain interactions with external systems or services.  
  - **Summary**:  
    - **Key Findings**: Summarize the main insights from both static and dynamic analysis.  
    - **Recommendations**: Provide actionable recommendations based on the analysis.

- **Use clear, straightforward language** to describe each analysis point. Avoid technical jargon where possible to ensure accessibility.

- **Ensure the analysis narrative has a logical sequence**, starting with an overview of the repository, moving into static analysis, then dynamic analysis, and finally providing an overall summary.

- **Include placeholders** for variable values in the format [[variable-name]]. For example:  
  - For the repository files, use [[files]].

- **Do not include the purpose or instructions sections in your output**. Only provide the analysis report.

- **Your output must be in XML format**, strictly adhering to the structure shown in the examples provided.

- **Exclude CDATA sections** from your output to maintain a clean and readable structure.

- **Respond exclusively with the XML formatted output** containing only the analysis sections without any additional narrative or explanation.

- **If the user input does not follow the provided input-format**, infer the purpose, required sections, and variables from the user's description.

- **Ensure all placeholders, and examples are included** and properly formatted. Validate the prompt to confirm:  
  - All placeholders are included and correctly formatted.  
  - Examples are consistent with the expected output structure.

---

## Sections

### Static Analysis

- **Code Structure**: Analyze the overall organization of the codebase.  
- **Code Complexity**: Assess cyclomatic complexity, code duplication, and maintainability.  
- **Potential Issues**: Identify any security vulnerabilities, coding errors, or anti-patterns.

### Dynamic Analysis

- **Runtime Behavior**: Describe how the code behaves at runtime.  
- **Performance**: Highlight performance bottlenecks or inefficiencies.  
- **Interactions**: Explain interactions with external systems or services.

### Summary

- **Key Findings**: Summarize the main insights from both static and dynamic analysis.  
- **Recommendations**: Provide actionable recommendations based on the analysis.

---

## Examples

### Example (Static Analysis)

- **Code Structure**: The repository has a well-organized structure with clear separation of concerns between modules.  
- **Code Complexity**: Cyclomatic complexity averages at 15, with some modules having higher complexity due to nested loops and conditionals.  
- **Potential Issues**: A potential SQL injection vulnerability was found in the user authentication module.

### Example (Dynamic Analysis)

- **Runtime Behavior**: The application exhibits high CPU usage during data processing due to inefficient algorithms.  
- **Performance**: Memory leaks were detected in the cache management system, leading to performance degradation over time.  
- **Interactions**: The API calls to an external payment gateway are causing significant delays in transaction processing.

### Example (Summary)

- **Key Findings**: The codebase has good structure but needs attention to performance optimization and security concerns.  
- **Recommendations**:  
  1. Implement better error handling and input validation to prevent potential security issues.  
  2. Optimize algorithms to reduce CPU and memory usage.  
  3. Consider asynchronous processing for external API calls to improve responsiveness.

---

## User Prompt

Here are the files from the repository: [[files]].

Please analyze these inputs to produce:  
- A narrative description of the static and dynamic analysis findings.  
- A summary with key insights and recommendations.
        """
        
        return PromptTemplate.from_template(template_prompt)
        
    def _load_system_architecture_template(self):
        code = ""
        template_prompt = ""
        
        return PromptTemplate.from_template(template_prompt)
    def _load_template(self):
        """
        Load the prompt template from the specified file.
        
        :return: PromptTemplate object
        """
        with open(self.template_path, 'r') as f:
            template_content = f.read()
        return PromptTemplate.from_template(template_content)

    def edit_template(self, new_content: str):
        """
        Edit the prompt template with new content.
        
        :param new_content: New content for the template
        """
        self.file_editor._run(FileEditorInput(
            file_path=self.template_path,
            new_content=new_content
        ))

    def run(self, prompt):
        """
        Execute the LLM interaction with the given prompt.
        
        :param prompt: User prompt
        :return: Response message
        """
        prompt_template = self._load_template()
        formatted_prompt = prompt_template.format(prompt=prompt)
        llm_response = self.llm_wrapper.generate_response(formatted_prompt, {})

        if llm_response:
            with open(self.text_path, 'a') as f:
                f.write(f"\nUser: {prompt}\nLLM: {llm_response}\n")

            second_prompt = f"{formatted_prompt}\n{llm_response}"
            second_llm_response = self.llm_wrapper.generate_response(second_prompt, {})

            if second_llm_response:
                with open(self.text_path, 'a') as f:
                    f.write(f"\nLLM (second response): {second_llm_response}\n")
                return f"Responses saved to {self.text_path}"
            else:
                return f"First response saved to {self.text_path}, but second response failed."
        else:
            return "LLM response failed." 