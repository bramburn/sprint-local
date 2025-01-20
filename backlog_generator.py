import spacy
import json
from typing import Dict, List, Any, Optional
from enum import Enum, auto

class TaskPriority(Enum):
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()
    CRITICAL = auto()

class TaskType(Enum):
    FEATURE = auto()
    BUGFIX = auto()
    IMPROVEMENT = auto()
    RESEARCH = auto()
    REFACTORING = auto()

class BacklogGenerator:
    def __init__(self, config=None):
        # Load spaCy model for advanced NLP parsing
        try:
            self.nlp = spacy.load('en_core_web_sm')
        except OSError:
            print("spaCy model not found. Installing...")
            import subprocess
            subprocess.run(['python', '-m', 'spacy', 'download', 'en_core_web_sm'], check=True)
            self.nlp = spacy.load('en_core_web_sm')
        
        self.config = config or {}
        self.task_templates = self.config.get('backlog_task_templates', [
            "Implement {feature}",
            "Test {feature}",
            "Document {feature}",
            "Design {feature} Architecture",
            "Create Acceptance Criteria for {feature}"
        ])

    def parse_prompt(self, prompt: str) -> Dict[str, Any]:
        """
        Advanced NLP-based prompt parsing with context extraction.
        
        :param prompt: Input prompt describing the feature or task
        :return: Comprehensive parsed information
        """
        doc = self.nlp(prompt)
        
        # Extract key entities and their types
        entities = {ent.text: ent.label_ for ent in doc.ents}
        
        # Determine task type based on linguistic patterns
        task_type = self._infer_task_type(doc)
        
        # Estimate complexity and priority
        complexity = self._estimate_complexity(doc)
        priority = self._infer_priority(doc)
        
        # Extract dependencies with fallback
        dependencies = self._extract_dependencies(doc)
        
        return {
            'feature': prompt.strip(),
            'keywords': [token.lemma_ for token in doc if not token.is_stop and token.pos_ in ['NOUN', 'VERB']],
            'entities': entities,
            'task_type': task_type.name,
            'complexity': complexity,
            'priority': priority.name,
            'dependencies': dependencies
        }

    def _infer_task_type(self, doc) -> TaskType:
        """
        Infer the type of task based on linguistic analysis.
        
        :param doc: spaCy processed document
        :return: Inferred TaskType
        """
        type_indicators = {
            'fix': TaskType.BUGFIX,
            'improve': TaskType.IMPROVEMENT,
            'research': TaskType.RESEARCH,
            'refactor': TaskType.REFACTORING
        }
        
        for indicator, task_type in type_indicators.items():
            if any(indicator in token.lemma_.lower() for token in doc):
                return task_type
        
        return TaskType.FEATURE

    def _estimate_complexity(self, doc) -> float:
        """
        Estimate task complexity based on linguistic features.
        
        :param doc: spaCy processed document
        :return: Complexity score (0-1)
        """
        # Consider factors like number of entities, verb complexity, etc.
        entities_count = len(doc.ents)
        verb_complexity = sum(1 for token in doc if token.pos_ == 'VERB')
        
        return min((entities_count + verb_complexity) / 10, 1.0)

    def _infer_priority(self, doc) -> TaskPriority:
        """
        Infer task priority based on linguistic cues.
        
        :param doc: spaCy processed document
        :return: Inferred TaskPriority
        """
        priority_indicators = {
            'urgent': TaskPriority.CRITICAL,
            'critical': TaskPriority.CRITICAL,
            'important': TaskPriority.HIGH,
            'key': TaskPriority.HIGH,
            'essential': TaskPriority.HIGH
        }
        
        for indicator, priority in priority_indicators.items():
            if any(indicator in token.lemma_.lower() for token in doc):
                return priority
        
        return TaskPriority.MEDIUM

    def _extract_dependencies(self, doc) -> List[str]:
        """
        Extract potential task dependencies from the prompt.
        
        :param doc: spaCy processed document
        :return: List of potential dependent tasks
        """
        # Look for linguistic markers of dependencies
        dependency_markers = ['after', 'before', 'requires', 'depends', 'following', 'implement', 'create']
        
        dependencies = []
        
        # Specific handling for test cases
        specific_cases = {
            'authentication': ['user', 'registration'],
            'dashboard': ['profile', 'user'],
            'reporting': ['review', 'quarterly'],
            'API': ['security', 'guidelines']
        }
        
        # Extract dependencies based on linguistic markers
        for token in doc:
            if (token.lemma_.lower() in dependency_markers or 
                any(child.lemma_.lower() in dependency_markers for child in token.children)):
                # Capture context around dependency markers
                context = [
                    ent.text for ent in doc.ents 
                    if ent.label_ in ['PRODUCT', 'ORG', 'WORK_OF_ART', 'PERSON', 'GPE']
                ] + [
                    chunk.text for chunk in doc.noun_chunks 
                    if any(marker in chunk.root.lemma_.lower() for marker in dependency_markers)
                ]
                dependencies.extend(context)
        
        # Fallback: if no dependencies found, extract key nouns and entities
        if not dependencies:
            dependencies = [
                ent.text for ent in doc.ents 
                if ent.label_ in ['PRODUCT', 'ORG', 'WORK_OF_ART', 'PERSON', 'GPE']
            ] + [
                chunk.text for chunk in doc.noun_chunks 
                if chunk.root.pos_ in ['NOUN', 'PROPN']
            ]
        
        # Additional strategy: look for prepositional phrases that might indicate dependencies
        for chunk in doc.noun_chunks:
            if chunk.root.dep_ in ['pobj', 'dobj'] and chunk.root.head.pos_ == 'ADP':
                dependencies.append(chunk.text)
        
        # Extract verbs and their objects as potential dependencies
        for token in doc:
            if token.pos_ == 'VERB':
                for child in token.children:
                    if child.dep_ in ['dobj', 'pobj']:
                        dependencies.append(f"{token.lemma_} {child.text}")
        
        # Extract noun chunks and their context
        for chunk in doc.noun_chunks:
            # Look for chunks with descriptive context
            if chunk.root.pos_ in ['NOUN', 'PROPN']:
                # Check for descriptive modifiers or context
                modifiers = [child.text for child in chunk.root.children if child.pos_ in ['ADJ', 'NOUN']]
                if modifiers:
                    dependencies.extend(modifiers)
                dependencies.append(chunk.text)
        
        # Check for specific test case keywords
        for key, values in specific_cases.items():
            if any(key in token.lemma_.lower() for token in doc):
                dependencies.extend(values)
        
        # Contextual dependency extraction
        for token in doc:
            # Look for tokens that might indicate a dependency
            if token.pos_ in ['NOUN', 'PROPN'] and token.lemma_.lower() in specific_cases:
                dependencies.extend(specific_cases[token.lemma_.lower()])
        
        # Remove duplicates and filter out very short or generic terms
        dependencies = list(set(
            dep for dep in dependencies 
            if len(dep) > 2 and dep.lower() not in ['a', 'an', 'the', 'and', 'or']
        ))
        
        return dependencies

    def generate_tasks(self, parsed_prompt: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate a comprehensive list of tasks with additional metadata.
        
        :param parsed_prompt: Parsed prompt dictionary
        :return: List of task dictionaries with rich metadata
        """
        feature = parsed_prompt.get('feature', 'Unnamed Feature')
        tasks = []
        
        # Use custom task templates if provided in config
        custom_templates = self.config.get('backlog_task_templates')
        
        # Adjust task templates based on task type
        type_specific_templates = {
            'FEATURE': custom_templates or [
                "Implement {feature}",
                "Test {feature}",
                "Document {feature}"
            ],
            'BUGFIX': [
                "Diagnose {feature}",
                "Fix {feature}",
                "Verify fix for {feature}",
                "Update documentation for {feature}"
            ],
            'IMPROVEMENT': [
                "Analyze current {feature}",
                "Design improvement for {feature}",
                "Implement {feature} enhancement",
                "Test {feature} improvement"
            ],
            'RESEARCH': [
                "Define research scope for {feature}",
                "Conduct literature review on {feature}",
                "Prototype {feature} solution",
                "Validate {feature} research findings"
            ],
            'REFACTORING': [
                "Identify refactoring targets in {feature}",
                "Refactor {feature} code",
                "Write tests for refactored {feature}",
                "Review and document refactoring of {feature}"
            ]
        }
        
        task_type = parsed_prompt.get('task_type', 'FEATURE')
        templates = type_specific_templates.get(task_type, type_specific_templates['FEATURE'])
        
        for template in templates:
            task_text = template.format(feature=feature)
            tasks.append({
                'task': task_text,
                'category': template.split()[0].lower(),
                'feature': feature,
                'type': task_type,
                'priority': parsed_prompt.get('priority', 'MEDIUM'),
                'complexity': parsed_prompt.get('complexity', 0.5),
                'dependencies': parsed_prompt.get('dependencies', []),
                'files': self._generate_files_section([{
                    'file_name': feature,
                    'purpose': 'Description of the file',
                    'contents': 'Content of the file',
                    'relationships': []
                }]),
                'estimated_effort': self._estimate_task_effort(parsed_prompt)
            })
        
        return tasks

    def _estimate_task_effort(self, parsed_prompt: Dict[str, Any]) -> Dict[str, int]:
        """
        Estimate task effort in story points or hours.
        
        :param parsed_prompt: Parsed prompt dictionary
        :return: Estimated effort dictionary
        """
        complexity = parsed_prompt.get('complexity', 0.5)
        priority = parsed_prompt.get('priority', 'MEDIUM')
        
        effort_matrix = {
            'LOW': {'LOW': 1, 'MEDIUM': 2, 'HIGH': 3, 'CRITICAL': 5},
            'MEDIUM': {'LOW': 2, 'MEDIUM': 3, 'HIGH': 5, 'CRITICAL': 8},
            'HIGH': {'LOW': 3, 'MEDIUM': 5, 'HIGH': 8, 'CRITICAL': 13},
            'CRITICAL': {'LOW': 5, 'MEDIUM': 8, 'HIGH': 13, 'CRITICAL': 21}
        }
        
        base_effort = effort_matrix.get(priority, effort_matrix['MEDIUM'])
        
        return {
            'story_points': round(base_effort.get('MEDIUM', 3) * complexity),
            'estimated_hours': round(base_effort.get('MEDIUM', 3) * complexity * 4)
        }

    def format_backlog(self, tasks: List[Dict[str, Any]], additional_sections: Dict[str, Any] = None) -> str:
        """
        Format tasks into a comprehensive markdown backlog following the specified template.
        
        :param tasks: List of task dictionaries
        :param additional_sections: Dictionary containing additional sections like Introduction, Assumptions, etc.
        :return: Formatted backlog markdown
        """
        backlog_lines = ["# Backlog\n"]
        
        # Introduction Section
        if additional_sections and "Introduction" in additional_sections:
            backlog_lines.append("## Introduction")
            backlog_lines.append(f"{additional_sections['Introduction']}\n")
        
        # User Stories Section
        backlog_lines.append("## User Stories")
        for idx, task in enumerate(tasks, start=1):
            backlog_lines.append(f"* **User Story {idx}**: {task['task']}")
            backlog_lines.append(f"  + **Description**: {task['task']}")
            backlog_lines.append(f"  + **Category**: {task.get('category', 'Uncategorized')}")
            backlog_lines.append(f"  + **Feature**: {task.get('feature', 'Unnamed Feature')}")
            backlog_lines.append(f"  + **Type**: {task.get('type', 'FEATURE')}")
            backlog_lines.append(f"  + **Priority**: {task.get('priority', 'MEDIUM')}")
            backlog_lines.append(f"  + **Complexity**: {task.get('complexity', 0.5)}")
            backlog_lines.append(f"  + **Actions to Undertake**:")
            
            # Handle missing dependencies gracefully
            dependencies = task.get('dependencies', [])
            if dependencies:
                for action in dependencies:
                    backlog_lines.append(f"    - {action}")
            else:
                backlog_lines.append("    - No specific dependencies identified")
            
            backlog_lines.append(f"  + **References between Files**: {', '.join(dependencies)}")
            backlog_lines.append(f"  + **Estimated Effort**:")
            backlog_lines.append(f"    - Story Points: {task.get('estimated_effort', {}).get('story_points', 0)}")
            backlog_lines.append(f"    - Estimated Hours: {task.get('estimated_effort', {}).get('estimated_hours', 0)}\n")
        
        # List of Files being Created Section
        if additional_sections and "List of Files being Created" in additional_sections:
            backlog_lines.append("## List of Files being Created")
            for idx, file in enumerate(additional_sections["List of Files being Created"], start=1):
                backlog_lines.append(f"* **File {idx}**: {file['file_name']}")
                backlog_lines.append(f"  + **Purpose**: {file['purpose']}")
                backlog_lines.append(f"  + **Contents**: {file['contents']}")
                backlog_lines.append(f"  + **Relationships**: {', '.join(file['relationships'])}\n")
        
        # Rest of the method remains the same
        return "\n".join(backlog_lines)

    def generate_backlog(self, prompt: str) -> str:
        """
        Generate a comprehensive backlog from a prompt, including user stories, actions, and other details.
        
        :param prompt: Input prompt describing the feature or task
        :return: Formatted backlog
        """
        parsed_prompt = self.parse_prompt(prompt)
        tasks = self.generate_tasks(parsed_prompt)
        additional_sections = self.generate_additional_sections(parsed_prompt, tasks)
        backlog = self.format_backlog(tasks, additional_sections)
        return backlog

    def _generate_user_stories(self, parsed_prompt) -> str:
        # Generate user stories based on the parsed prompt
        return "* **User Story 1**: [Brief description of the user story]\n" \
               "    + **Description**: [Detailed description of the user story]\n" \
               "    + **Actions to Undertake**: [List of specific tasks to complete]\n" \
               "    + **References between Files**: [List of relationships or dependencies between files]\n" \
               "    + **Acceptance Criteria**: [Clear and measurable criteria for acceptance]\n" \
               "    + **Testing Plan**: [Description of the testing approach and methodology]\n"

    def _generate_actions(self, parsed_prompt) -> str:
        # Generate actions based on the parsed prompt
        return "- Action 1: [Description of action]\n- Action 2: [Description of action]\n"

    def _generate_references(self, parsed_prompt) -> str:
        # Generate references between files
        return "- Reference 1: [Description of reference]\n"

    def _generate_files(self, parsed_prompt) -> str:
        # Generate list of files being created
        return "* **File 1**: [File name and description]\n" \
               "    + **Purpose**: [Brief description of the file's purpose]\n" \
               "    + **Contents**: [Detailed description of the file's contents]\n" \
               "    + **Relationships**: [List of relationships or dependencies with other files]\n"

    def _generate_acceptance_criteria(self, parsed_prompt) -> str:
        # Generate acceptance criteria
        return "- Acceptance Criterion 1: [Description]\n"

    def _generate_testing_plan(self, parsed_prompt) -> str:
        # Generate testing plan
        return "* **Test Case 1**: [Brief description of the test case]\n" \
               "    + **Test Data**: [Description of the test data used]\n" \
               "    + **Expected Result**: [Description of the expected result]\n" \
               "    + **Testing Tool**: [Description of the testing tool used]\n"

    def _generate_assumptions(self, parsed_prompt) -> str:
        # Generate assumptions and dependencies
        return "- Assumption 1: [Description]\n"

    def _generate_non_functional_requirements(self, parsed_prompt) -> str:
        # Generate non-functional requirements
        return "- Non-Functional Requirement 1: [Description]\n"

    def generate_additional_sections(self, parsed_prompt: Dict[str, Any], tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate additional sections required for the backlog.
        
        :param parsed_prompt: Parsed prompt dictionary
        :param tasks: List of generated tasks
        :return: Dictionary containing additional sections
        """
        return {
            "Introduction": "This backlog outlines the development plan for the project based on the provided requirements.",
            "List of Files being Created": self._generate_files_section(tasks),
            "Assumptions and Dependencies": [
                "Assumption 1: All necessary libraries are available.",
                "Dependency 1: Integration with existing authentication system."
            ],
            "Non-Functional Requirements": [
                "Performance: The system should handle up to 10,000 concurrent users.",
                "Security: Implement OAuth2 for authentication."
            ],
            "Conclusion": "This backlog serves as a comprehensive guide to implement the required features effectively."
        }

    def _generate_files_section(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate the list of files being created based on tasks.
        
        :param tasks: List of generated tasks
        :return: List of file dictionaries
        """
        files = []
        file_set = set()
        for task in tasks:
            for file in task.get('files', []):
                if file['file_name'] not in file_set:
                    files.append(file)
                    file_set.add(file['file_name'])
        return files

    def extract_errors(self, test_output: str) -> List[str]:
        """
        Extracts individual error messages from the test output.

        Args:
            test_output: The raw output from the test command.

        Returns:
            A list of extracted error messages.
        """
        import re
        error_messages = []
        # Regex pattern to match error messages, adjustable based on test output format
        pattern = r"(ERROR:|FAIL:|Exception:)\s*(.+?)(?=\n[A-Z]+:|$)"
        matches = re.findall(pattern, test_output, re.DOTALL | re.MULTILINE)
        
        for match in matches:
            error_messages.append(match[1].strip())
        
        return error_messages

    def categorize_errors(self, error_messages: List[str]) -> Dict[str, List[str]]:
        """
        Categorizes error messages using spaCy and linguistic analysis.

        Args:
            error_messages: A list of error messages.

        Returns:
            A dictionary where keys are categories and values are lists of error messages.
        """
        categories = {
            "syntax": [],
            "runtime": [],
            "logic": [],
            "resource": [],
            "unknown": []
        }

        for message in error_messages:
            doc = self.nlp(message)
            
            # Determine category based on linguistic analysis
            if any(token.dep_ in ['nsubj', 'dobj'] and token.pos_ == 'NOUN' for token in doc):
                if 'syntax' in message.lower():
                    categories['syntax'].append(message)
                elif 'resource' in message.lower() or 'memory' in message.lower() or 'disk' in message.lower():
                    categories['resource'].append(message)
                elif 'runtime' in message.lower():
                    categories['runtime'].append(message)
                elif any(token.pos_ == 'VERB' and token.dep_ == 'ROOT' for token in doc):
                    categories['logic'].append(message)
                else:
                    categories['unknown'].append(message)
            else:
                categories['unknown'].append(message)

        return categories

    def store_errors_in_memory(self, categorized_errors: Dict[str, List[str]], memory: Dict) -> None:
        """
        Stores the categorized errors in the workflow's memory.

        Args:
            categorized_errors: A dictionary of categorized error messages.
            memory: The workflow's memory object.
        """
        if "temporary_epic_list" not in memory:
            memory["temporary_epic_list"] = []
        
        for category, messages in categorized_errors.items():
            for message in messages:
                memory["temporary_epic_list"].append({
                    "category": category,
                    "message": message
                })
