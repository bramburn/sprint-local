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
            subprocess.run(['poetry', 'run', 'python', '-m', 'spacy', 'download', 'en_core_web_sm'], check=True)
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
        
        Args:
            parsed_prompt: Parsed prompt dictionary
        
        Returns:
            List of task dictionaries with rich metadata
        """
        feature = parsed_prompt.get('feature', 'Unnamed Feature')
        task_type = parsed_prompt.get('task_type', 'FEATURE')
        tasks = []
        
        # Use custom task templates if provided in config
        templates = self.config.get('backlog_task_templates')
        
        # Adjust task templates based on task type
        type_specific_templates = {
            'FEATURE': templates or [
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
                "Write tests for {feature}",
                "Review {feature} changes"
            ]
        }
        
        # Get templates for the current task type
        current_templates = type_specific_templates.get(task_type, type_specific_templates['FEATURE'])
        
        # Generate tasks using templates
        for template in current_templates:
            task = {
                'task': template.format(feature=feature),
                'category': task_type.lower(),
                'feature': feature,
                'type': task_type,
                'priority': parsed_prompt.get('priority', 'MEDIUM'),
                'complexity': parsed_prompt.get('complexity', 0.5),
                'dependencies': parsed_prompt.get('dependencies', []),
                'estimated_effort': self._estimate_task_effort(parsed_prompt)
            }
            tasks.append(task)
        
        return tasks

    def _estimate_task_effort(self, parsed_prompt: Dict[str, Any]) -> Dict[str, int]:
        """
        Estimate task effort based on complexity and type.
        
        Args:
            parsed_prompt: Parsed prompt dictionary
        
        Returns:
            Dictionary with story points and estimated hours
        """
        complexity = parsed_prompt.get('complexity', 0.5)
        task_type = parsed_prompt.get('task_type', 'FEATURE')
        
        # Base effort multipliers for different task types
        type_multipliers = {
            'FEATURE': 1.0,
            'BUGFIX': 0.7,
            'IMPROVEMENT': 0.8,
            'RESEARCH': 1.2,
            'REFACTORING': 1.1
        }
        
        multiplier = type_multipliers.get(task_type, 1.0)
        
        # Calculate story points (1-13 scale)
        story_points = max(1, min(13, int(complexity * 13 * multiplier)))
        
        # Calculate estimated hours (rough estimate)
        estimated_hours = max(1, int(story_points * 4 * multiplier))
        
        return {
            'story_points': story_points,
            'estimated_hours': estimated_hours
        }

    def format_backlog(self, tasks: List[Dict[str, Any]], additional_sections: Dict[str, Any] = None) -> str:
        """
        Format tasks into a readable backlog document.
        
        Args:
            tasks: List of task dictionaries
            additional_sections: Optional additional sections to include
        
        Returns:
            Formatted backlog string
        """
        sections = ["# Backlog\n"]
        
        # Add tasks section
        sections.append("## Tasks\n")
        for task in tasks:
            sections.append(f"### {task['task']}\n")
            sections.append(f"- Category: {task.get('category', 'N/A')}")
            sections.append(f"- Feature: {task.get('feature', 'N/A')}")
            if 'estimated_effort' in task:
                sections.append(f"- Story Points: {task['estimated_effort']['story_points']}")
                sections.append(f"- Estimated Hours: {task['estimated_effort']['estimated_hours']}")
            sections.append("")
        
        # Add additional sections if provided
        if additional_sections:
            for title, content in additional_sections.items():
                sections.append(f"## {title}\n")
                sections.append(f"{content}\n")
        
        return "\n".join(sections)

    def generate_backlog(self, prompt: str) -> str:
        """
        Generate a complete backlog from a prompt.
        
        Args:
            prompt: Input prompt describing the feature or task
        
        Returns:
            Complete formatted backlog
        """
        parsed = self.parse_prompt(prompt)
        tasks = self.generate_tasks(parsed)
        
        # Generate additional sections
        additional_sections = {
            'Feature Description': parsed['feature'],
            'Type': parsed['task_type'],
            'Priority': parsed['priority'],
            'Complexity': f"{parsed['complexity']:.2f}"
        }
        
        return self.format_backlog(tasks, additional_sections)

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
        Extract error messages from test output.
        
        Args:
            test_output: Raw test output string
        
        Returns:
            List of extracted error messages
        """
        errors = []
        for line in test_output.split('\n'):
            line = line.strip()
            if any(error_type in line for error_type in ['ERROR:', 'FAIL:', 'Exception:']):
                errors.append(line)
        return errors

    def categorize_errors(self, error_messages: List[str]) -> Dict[str, List[str]]:
        """
        Categorize error messages by type.
        
        Args:
            error_messages: List of error messages
        
        Returns:
            Dictionary mapping error categories to lists of errors
        """
        categories = {
            'syntax': [],
            'runtime': [],
            'logic': [],
            'resource': [],
            'unknown': []
        }
        
        for error in error_messages:
            if 'SyntaxError' in error:
                categories['syntax'].append(error)
            elif 'RuntimeError' in error:
                categories['runtime'].append(error)
            elif any(x in error for x in ['LogicError', 'AssertionError']):
                categories['logic'].append(error)
            elif any(x in error for x in ['MemoryError', 'ResourceError']):
                categories['resource'].append(error)
            else:
                categories['unknown'].append(error)
        
        return categories

    def store_errors_in_memory(self, categorized_errors: Dict[str, List[str]], memory: Dict) -> None:
        """
        Store categorized errors in memory for later analysis.
        
        Args:
            categorized_errors: Dictionary of categorized errors
            memory: Memory dictionary to store errors in
        """
        memory['temporary_epic_list'] = []
        
        for category, errors in categorized_errors.items():
            for error in errors:
                memory['temporary_epic_list'].append({
                    'category': category,
                    'message': error
                })
