"""
Reflection Agent: An intelligent code analysis and solution generation toolkit.

This module provides a comprehensive workflow for analyzing code repositories, 
extracting insights, and generating solutions based on natural language prompts.
"""

from .workflow import ReflectionWorkflow
from .models.schemas import (
    FileAnalysis, 
    CodeSolution, 
    AgentOutput
)
from .utils.repo_scanner import RepositoryScanner
from .utils.vector_store_creator import VectorStoreCreator

__all__ = [
    'ReflectionWorkflow',
    'RepositoryScanner',
    'VectorStoreCreator',
    'FileAnalysis',
    'CodeSolution',
    'AgentOutput'
]