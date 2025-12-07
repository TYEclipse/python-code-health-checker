"""
Python Code Health Checker - A tool for analyzing Python code structure health.

This package provides utilities for scanning Python projects and identifying
files and functions that exceed specified line count thresholds.
"""

__version__ = '1.0.0'
__author__ = 'Manus AI'
__license__ = 'MIT'

from .code_health_checker import (
    CodeHealthChecker,
    CodeLineCounter,
    FunctionExtractor,
    FileIssue,
    FunctionIssue,
)

__all__ = [
    'CodeHealthChecker',
    'CodeLineCounter',
    'FunctionExtractor',
    'FileIssue',
    'FunctionIssue',
]
