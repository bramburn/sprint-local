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
    try:
        files = scan_directory(repo_path)
        
        # Comprehensive framework markers
        framework_markers = {
            # Python Testing Frameworks
            TestFramework.PYTEST: [
                'test_', 'conftest.py', 'pytest.ini', 
                'tests/', 'test/', '__pycache__/test_'
            ],
            TestFramework.UNITTEST: [
                'unittest', 'test_case', 'test_', 
                'python -m unittest', 'TestCase'
            ],
            
            # JavaScript/TypeScript Testing Frameworks
            TestFramework.JEST: [
                'jest.config.js', '__tests__', 
                'test.js', 'test.ts', 'jest.setup.js'
            ],
            TestFramework.VITEST: [
                'vitest.config.ts', 'vitest.config.js', 
                'test.vitest.ts', 'test.vitest.js'
            ],
            
            # Other Frameworks
            TestFramework.NPM: ['package.json', 'node_modules/']
        }
        
        # Scoring system for framework detection
        framework_scores = {framework: 0 for framework in framework_markers.keys()}
        
        # Score frameworks based on marker presence
        for framework, markers in framework_markers.items():
            for marker in markers:
                if any(marker in file.lower() for file in files):
                    framework_scores[framework] += 1
        
        # Determine the most likely framework
        max_score = max(framework_scores.values())
        
        if max_score == 0:
            return FrameworkDetectionResult(
                framework=TestFramework.UNKNOWN,
                confidence=0.1,
                detection_method='no_markers'
            )
        
        detected_frameworks = [
            framework for framework, score in framework_scores.items() 
            if score == max_score
        ]
        
        # Handle multiple framework detection
        if len(detected_frameworks) > 1:
            return FrameworkDetectionResult(
                framework=TestFramework.UNKNOWN,
                confidence=0.4,
                detection_method='multiple_markers'
            )
        
        # Single framework detected
        detected_framework = detected_frameworks[0]
        confidence = min(1.0, max_score / len(framework_markers[detected_framework]) * 0.8)
        
        return FrameworkDetectionResult(
            framework=detected_framework,
            confidence=confidence,
            detection_method='marker_based'
        )
    
    except Exception as e:
        # Log the error and return unknown framework
        return FrameworkDetectionResult(
            framework=TestFramework.UNKNOWN,
            confidence=0.0,
            detection_method=f'error: {str(e)}'
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
