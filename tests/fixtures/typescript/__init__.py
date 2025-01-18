"""
TypeScript test fixtures for code_analyzer tests.

This package contains sample TypeScript, JavaScript, TSX, and JSX files
used for testing the code_analyzer's TypeScript-related functionality.
"""

from pathlib import Path

FIXTURES_DIR = Path(__file__).parent
SAMPLE_TS = FIXTURES_DIR / 'sample.ts'
SAMPLE_TSX = FIXTURES_DIR / 'sample.tsx'
SAMPLE_JS = FIXTURES_DIR / 'sample.js'
SAMPLE_JSX = FIXTURES_DIR / 'sample.jsx' 