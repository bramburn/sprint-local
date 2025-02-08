import os
import re
from typing import List, Optional
from .schemas import TestingAgentState, TestFramework, FrameworkDetectionResult
from src.utils.dir_tool import scan_directory

def detect_framework(repo_path: str) -> FrameworkDetectionResult:
    """
    Detect testing framework based on repository structure.
    
    Args:
        repo_path: Path to the repository
    
    Returns:
        Framework detection result with confidence
    """
    files = scan_directory(repo_path)
    
    framework_markers = {
        TestFramework.PYTEST: ['test_', 'conftest.py', 'pytest.ini'],
        TestFramework.JEST: ['jest.config.js', '__tests__'],
        TestFramework.VITEST: ['vitest.config.ts', 'vitest.config.js'],
        TestFramework.NPM: ['package.json']
    }
    
    detected_frameworks = []
    
    for framework, markers in framework_markers.items():
        if any(any(marker in file for marker in markers) for file in files):
            detected_frameworks.append(framework)
    
    if len(detected_frameworks) == 1:
        return FrameworkDetectionResult(
            framework=detected_frameworks[0],
            confidence=0.8,
            detection_method='marker_based'
        )
    elif len(detected_frameworks) > 1:
        return FrameworkDetectionResult(
            framework=TestFramework.UNKNOWN,
            confidence=0.4,
            detection_method='multiple_markers'
        )
    else:
        return FrameworkDetectionResult(
            framework=TestFramework.UNKNOWN,
            confidence=0.1,
            detection_method='no_markers'
        )

def calculate_confidence(state: TestingAgentState) -> float:
    """
    Calculate confidence based on framework detection and repository characteristics.
    
    Args:
        state: Current testing agent state
    
    Returns:
        Confidence score
    """
    base_confidence = 0.5
    
    # Additional confidence modifiers
    modifiers = {
        TestFramework.PYTEST: 0.3,
        TestFramework.JEST: 0.3,
        TestFramework.VITEST: 0.3,
        TestFramework.NPM: 0.2,
        TestFramework.UNKNOWN: -0.2
    }
    
    return min(1.0, max(0.0, base_confidence + modifiers.get(state.framework, -0.2)))
