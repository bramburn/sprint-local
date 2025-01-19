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
        
        return {
            'feature': prompt.strip(),
            'keywords': [token.lemma_ for token in doc if not token.is_stop and token.pos_ in ['NOUN', 'VERB']],
            'entities': entities,
            'task_type': task_type.name,
            'complexity': complexity,
            'priority': priority.name,
            'dependencies': self._extract_dependencies(doc)
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
        dependency_markers = ['after', 'before', 'requires', 'depends', 'following']
        
        dependencies = []
        for token in doc:
            # Check if the token or its children match dependency markers
            if (token.lemma_.lower() in dependency_markers or 
                any(child.lemma_.lower() in dependency_markers for child in token.children)):
                # Capture nouns or noun chunks around the dependency marker
                context = [
                    ent.text for ent in doc.ents if ent.label_ in ['PRODUCT', 'ORG', 'WORK_OF_ART']
                ] + [
                    chunk.text for chunk in doc.noun_chunks 
                    if any(marker in chunk.root.lemma_.lower() for marker in dependency_markers)
                ]
                dependencies.extend(context)
        
        return list(set(dependencies))  # Remove duplicates

    def generate_tasks(self, parsed_prompt: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate a comprehensive list of tasks with additional metadata.
        
        :param parsed_prompt: Parsed prompt dictionary
        :return: List of task dictionaries with rich metadata
        """
        feature = parsed_prompt.get('feature', 'Unnamed Feature')
        tasks = []
        
        # Adjust task templates based on task type
        type_specific_templates = {
            'FEATURE': [
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

    def format_backlog(self, tasks: List[Dict[str, Any]]) -> str:
        """
        Format tasks into a comprehensive markdown backlog.
        
        :param tasks: List of task dictionaries
        :return: Formatted backlog markdown
        """
        backlog_lines = ["# Backlog\n"]
        
        for task in tasks:
            backlog_lines.append(f"## {task['task']}")
            backlog_lines.append(f"- **Category**: {task['category']}")
            backlog_lines.append(f"- **Feature**: {task['feature']}")
            backlog_lines.append(f"- **Type**: {task['type']}")
            backlog_lines.append(f"- **Priority**: {task['priority']}")
            backlog_lines.append(f"- **Complexity**: {task['complexity']:.2f}")
            
            if task['dependencies']:
                backlog_lines.append(f"- **Dependencies**: {', '.join(task['dependencies'])}")
            
            backlog_lines.append(f"- **Estimated Effort**:")
            backlog_lines.append(f"  - Story Points: {task['estimated_effort']['story_points']}")
            backlog_lines.append(f"  - Estimated Hours: {task['estimated_effort']['estimated_hours']}\n")
        
        return "\n".join(backlog_lines)

    def generate_backlog(self, prompt: str) -> str:
        """
        Convenience method to generate a comprehensive backlog from a prompt.
        
        :param prompt: Input prompt describing the feature or task
        :return: Formatted backlog
        """
        parsed_prompt = self.parse_prompt(prompt)
        tasks = self.generate_tasks(parsed_prompt)
        return self.format_backlog(tasks)
