import json
from typing import Dict, List, Any

class BacklogGenerator:
    def __init__(self, config=None):
        """
        Initialize the BacklogGenerator with optional configuration.
        
        :param config: Configuration for backlog generation, defaults to None
        """
        self.config = config or {}
        self.task_templates = self.config.get('backlog_task_templates', [
            "Implement {feature}",
            "Test {feature}",
            "Document {feature}"
        ])

    def parse_prompt(self, prompt: str) -> Dict[str, Any]:
        """
        Parse the input prompt and extract key information.
        
        :param prompt: Input prompt describing the feature or task
        :return: A dictionary containing parsed information
        """
        # Basic parsing - can be enhanced with more sophisticated NLP techniques
        return {
            'feature': prompt.strip(),
            'keywords': prompt.lower().split()
        }

    def generate_tasks(self, parsed_prompt: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Generate a list of tasks based on the parsed prompt.
        
        :param parsed_prompt: Parsed prompt dictionary
        :return: A list of task dictionaries
        """
        feature = parsed_prompt.get('feature', 'Unnamed Feature')
        
        tasks = []
        for template in self.task_templates:
            tasks.append({
                'task': template.format(feature=feature),
                'category': template.split()[0].lower(),
                'feature': feature
            })
        
        return tasks

    def format_backlog(self, tasks: List[Dict[str, str]]) -> str:
        """
        Format the list of tasks into a structured backlog.
        
        :param tasks: List of task dictionaries
        :return: Formatted backlog as a string
        """
        backlog_lines = ["# Backlog\n"]
        
        for task in tasks:
            backlog_lines.append(f"## {task['task']}")
            backlog_lines.append(f"- **Category**: {task['category']}")
            backlog_lines.append(f"- **Feature**: {task['feature']}\n")
        
        return "\n".join(backlog_lines)

    def generate_backlog(self, prompt: str) -> str:
        """
        Convenience method to generate a backlog from a prompt.
        
        :param prompt: Input prompt describing the feature or task
        :return: Formatted backlog
        """
        parsed_prompt = self.parse_prompt(prompt)
        tasks = self.generate_tasks(parsed_prompt)
        return self.format_backlog(tasks)
