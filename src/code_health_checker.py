#!/usr/bin/env python3
"""
Python Code Health Checker

Analyzes Python projects to identify files and functions exceeding specified
line count thresholds. Generates reports in multiple formats (console, JSON, HTML).
"""

import ast
import os
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, asdict, field
import re


@dataclass
class FunctionIssue:
    """Data structure for function/method exceeding threshold"""
    name: str
    start_line: int
    end_line: int
    effective_lines: int
    type: str  # 'function' or 'method'


@dataclass
class FileIssue:
    """Data structure for file exceeding threshold"""
    file_path: str
    total_lines: int
    effective_lines: int
    functions: List[FunctionIssue] = field(default_factory=list)


class CodeLineCounter:
    """
    Counts effective lines of code in Python source.
    
    Effective lines exclude:
    - Empty lines
    - Single-line comments (starting with #)
    - Docstrings (first statement of module/class/function)
    """
    
    def __init__(self, source_code: str, file_path: str = ""):
        self.source_code = source_code
        self.file_path = file_path
        self.lines = source_code.splitlines()
        self.docstring_ranges: Set[int] = set()
        self._identify_docstrings()
    
    def _identify_docstrings(self) -> None:
        """Identify all docstring line ranges using AST."""
        try:
            tree = ast.parse(self.source_code)
        except SyntaxError:
            return
        
        docstring_nodes = self._extract_docstring_nodes(tree)
        for node in docstring_nodes:
            if hasattr(node, 'lineno') and hasattr(node, 'end_lineno'):
                for i in range(node.lineno - 1, node.end_lineno):
                    if i < len(self.lines):
                        self.docstring_ranges.add(i)
    
    def _extract_docstring_nodes(self, node: ast.AST) -> List[ast.Expr]:
        """Extract all docstring nodes from AST."""
        docstrings = []
        
        # Module-level docstring
        if isinstance(node, ast.Module) and node.body:
            first_stmt = node.body[0]
            if isinstance(first_stmt, ast.Expr) and isinstance(first_stmt.value, ast.Constant):
                if isinstance(first_stmt.value.value, str):
                    docstrings.append(first_stmt)
        
        # Class and function docstrings
        for child in ast.walk(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if child.body and isinstance(child.body[0], ast.Expr):
                    first_stmt = child.body[0]
                    if isinstance(first_stmt.value, ast.Constant):
                        if isinstance(first_stmt.value.value, str):
                            docstrings.append(first_stmt)
        
        return docstrings
    
    def count_effective_lines(self, start_line: int = 0, end_line: Optional[int] = None) -> int:
        """Count effective lines in specified range."""
        if end_line is None:
            end_line = len(self.lines)
        
        effective_count = 0
        for i in range(start_line, min(end_line, len(self.lines))):
            line = self.lines[i]
            stripped = line.strip()
            
            # Skip docstring lines
            if i in self.docstring_ranges:
                continue
            
            # Skip empty lines
            if not stripped:
                continue
            
            # Skip comment lines
            if stripped.startswith('#'):
                continue
            
            effective_count += 1
        
        return effective_count


class FunctionExtractor(ast.NodeVisitor):
    """Extract function and method information from AST."""
    
    def __init__(self, source_code: str):
        self.source_code = source_code
        self.functions: List[Dict] = []
        self.counter = CodeLineCounter(source_code)
        self.current_class: Optional[str] = None
    
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._process_function(node)
        self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._process_function(node)
        self.generic_visit(node)
    
    def _process_function(self, node: ast.FunctionDef) -> None:
        start_line = node.lineno - 1
        end_line = node.end_lineno
        
        effective_lines = self.counter.count_effective_lines(start_line, end_line)
        func_type = 'method' if self.current_class else 'function'
        
        self.functions.append({
            'name': node.name,
            'type': func_type,
            'class': self.current_class,
            'start_line': node.lineno,
            'end_line': node.end_lineno,
            'effective_lines': effective_lines
        })


class CodeHealthChecker:
    """Main checker class for analyzing code health."""
    
    def __init__(self, 
                 root_dir: str,
                 file_threshold: int = 500,
                 function_threshold: int = 50,
                 exclude_dirs: Optional[List[str]] = None,
                 exclude_patterns: Optional[List[str]] = None):
        self.root_dir = Path(root_dir)
        self.file_threshold = file_threshold
        self.function_threshold = function_threshold
        self.exclude_dirs = exclude_dirs or [
            '__pycache__', '.git', '.venv', 'venv', 'env',
            'node_modules', '.pytest_cache', '.tox', 'dist', 'build',
            '.mypy_cache', '.coverage'
        ]
        self.exclude_patterns = exclude_patterns or [
            r'.*\.pyc$',
            r'.*__pycache__.*',
            r'.*\.egg-info.*'
        ]
        self.issues: List[FileIssue] = []
    
    def should_exclude(self, file_path: Path) -> bool:
        """Check if file should be excluded."""
        for exclude_dir in self.exclude_dirs:
            if exclude_dir.rstrip('*') in file_path.parts:
                return True
        
        file_str = str(file_path)
        for pattern in self.exclude_patterns:
            if re.match(pattern, file_str):
                return True
        
        return False
    
    def scan(self) -> None:
        """Scan project directory for Python files."""
        py_files = list(self.root_dir.rglob('*.py'))
        
        for file_path in py_files:
            if self.should_exclude(file_path):
                continue
            
            try:
                self._check_file(file_path)
            except Exception as e:
                print(f"Warning: Error processing {file_path}: {e}", file=sys.stderr)
    
    def _check_file(self, file_path: Path) -> None:
        """Check a single Python file."""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            source_code = f.read()
        
        counter = CodeLineCounter(source_code, str(file_path))
        total_lines = len(counter.lines)
        effective_lines = counter.count_effective_lines()
        
        # Extract function information
        extractor = FunctionExtractor(source_code)
        try:
            tree = ast.parse(source_code)
            extractor.visit(tree)
        except SyntaxError:
            extractor.functions = []
        
        # Check if file exceeds threshold
        file_issue = None
        if effective_lines > self.file_threshold:
            file_issue = FileIssue(
                file_path=str(file_path.relative_to(self.root_dir)),
                total_lines=total_lines,
                effective_lines=effective_lines
            )
        
        # Check if any functions exceed threshold
        for func_info in extractor.functions:
            if func_info['effective_lines'] > self.function_threshold:
                func_issue = FunctionIssue(
                    name=func_info['name'],
                    start_line=func_info['start_line'],
                    end_line=func_info['end_line'],
                    effective_lines=func_info['effective_lines'],
                    type=func_info['type']
                )
                
                if file_issue is None:
                    file_issue = FileIssue(
                        file_path=str(file_path.relative_to(self.root_dir)),
                        total_lines=total_lines,
                        effective_lines=effective_lines
                    )
                
                file_issue.functions.append(func_issue)
        
        if file_issue is not None:
            self.issues.append(file_issue)
    
    def generate_json_report(self, output_file: str) -> None:
        """Generate JSON format report."""
        report = {
            'summary': {
                'total_issues': len(self.issues),
                'files_exceeding_threshold': len(self.issues),
                'functions_exceeding_threshold': sum(len(issue.functions) for issue in self.issues),
                'file_threshold': self.file_threshold,
                'function_threshold': self.function_threshold
            },
            'issues': [asdict(issue) for issue in self.issues]
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"JSON report generated: {output_file}")
    
    def generate_html_report(self, output_file: str) -> None:
        """Generate HTML format report."""
        html_lines = [
            '<!DOCTYPE html>',
            '<html lang="zh-CN">',
            '<head>',
            '    <meta charset="UTF-8">',
            '    <meta name="viewport" content="width=device-width, initial-scale=1.0">',
            '    <title>Python Code Health Report</title>',
            '    <style>',
            '        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }',
            '        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }',
            '        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 4px; }',
            '        .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }',
            '        .summary-card { background: #f9f9f9; padding: 15px; border-left: 4px solid #667eea; border-radius: 4px; }',
            '        .summary-card h3 { margin: 0 0 10px 0; color: #666; font-size: 12px; }',
            '        .summary-card .value { font-size: 24px; font-weight: bold; color: #667eea; }',
            '        .file-section { margin: 20px 0; border: 1px solid #ddd; border-radius: 4px; }',
            '        .file-header { background: #f9f9f9; padding: 15px; cursor: pointer; display: flex; justify-content: space-between; }',
            '        .file-header:hover { background: #f0f0f0; }',
            '        .file-details { padding: 15px; display: none; }',
            '        .file-details.show { display: block; }',
            '        table { width: 100%; border-collapse: collapse; margin-top: 10px; }',
            '        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }',
            '        th { background: #f9f9f9; font-weight: bold; }',
            '        .warning { color: #dc3545; font-weight: bold; }',
            '        .no-issues { text-align: center; padding: 40px; color: #666; }',
            '    </style>',
            '</head>',
            '<body>',
            '    <div class="container">',
            '        <div class="header">',
            '            <h1>Python Code Health Check Report</h1>',
            '            <p>Automated code quality analysis</p>',
            '        </div>',
            '        <div class="summary">',
            f'            <div class="summary-card"><h3>Total Issues</h3><div class="value">{len(self.issues)}</div></div>',
            f'            <div class="summary-card"><h3>Files Exceeding</h3><div class="value">{len(self.issues)}</div></div>',
            f'            <div class="summary-card"><h3>Functions Exceeding</h3><div class="value">{sum(len(issue.functions) for issue in self.issues)}</div></div>',
            f'            <div class="summary-card"><h3>File Threshold</h3><div class="value">{self.file_threshold}</div></div>',
            f'            <div class="summary-card"><h3>Function Threshold</h3><div class="value">{self.function_threshold}</div></div>',
            '        </div>',
            '        <div class="content">',
        ]
        
        if not self.issues:
            html_lines.append('            <div class="no-issues">No code quality issues found!</div>')
        else:
            for issue in self.issues:
                html_lines.append(f'            <div class="file-section">')
                html_lines.append(f'                <div class="file-header" onclick="this.nextElementSibling.classList.toggle(\'show\')">')
                html_lines.append(f'                    <span><strong>{issue.file_path}</strong> ({issue.effective_lines}/{issue.total_lines} lines)</span>')
                html_lines.append(f'                    <span>▼</span>')
                html_lines.append(f'                </div>')
                html_lines.append(f'                <div class="file-details show">')
                
                if issue.effective_lines > self.file_threshold:
                    html_lines.append(f'                    <p><span class="warning">File exceeds threshold: {issue.effective_lines} > {self.file_threshold}</span></p>')
                
                if issue.functions:
                    html_lines.append('                    <table>')
                    html_lines.append('                        <thead><tr><th>Function</th><th>Type</th><th>Lines</th><th>Effective Lines</th></tr></thead>')
                    html_lines.append('                        <tbody>')
                    for func in issue.functions:
                        html_lines.append(f'                            <tr><td>{func.name}</td><td>{func.type}</td><td>{func.start_line}-{func.end_line}</td><td><span class="warning">{func.effective_lines}</span></td></tr>')
                    html_lines.append('                        </tbody>')
                    html_lines.append('                    </table>')
                
                html_lines.append('                </div>')
                html_lines.append('            </div>')
        
        html_lines.extend([
            '        </div>',
            '    </div>',
            '</body>',
            '</html>'
        ])
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(html_lines))
        
        print(f"HTML report generated: {output_file}")
    
    def generate_console_report(self) -> None:
        """Generate console format report."""
        print("\n" + "="*80)
        print("Python Code Health Check Report".center(80))
        print("="*80 + "\n")
        
        print("Summary")
        print("-" * 80)
        print(f"  Total issues: {len(self.issues)}")
        print(f"  Files exceeding threshold: {len(self.issues)}")
        print(f"  Functions exceeding threshold: {sum(len(issue.functions) for issue in self.issues)}")
        print(f"  File threshold: {self.file_threshold} lines")
        print(f"  Function threshold: {self.function_threshold} lines")
        print()
        
        if not self.issues:
            print("No code quality issues found!\n")
            return
        
        print("Issues Details")
        print("-" * 80)
        
        for idx, issue in enumerate(self.issues, 1):
            print(f"\n{idx}. {issue.file_path}")
            print(f"   Total lines: {issue.total_lines}, Effective lines: {issue.effective_lines}")
            
            if issue.effective_lines > self.file_threshold:
                print(f"   WARNING: File exceeds threshold: {issue.effective_lines} > {self.file_threshold}")
            
            if issue.functions:
                print(f"   Functions exceeding threshold:")
                for func in issue.functions:
                    print(f"     - {func.name} ({func.type})")
                    print(f"       Lines: {func.start_line}-{func.end_line}, Effective: {func.effective_lines}")
        
        print("\n" + "="*80 + "\n")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Python Code Health Checker',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('root_dir', help='Project root directory')
    parser.add_argument('--file-threshold', type=int, default=500, help='File threshold (default: 500)')
    parser.add_argument('--function-threshold', type=int, default=50, help='Function threshold (default: 50)')
    parser.add_argument('--exclude-dir', action='append', dest='exclude_dirs', help='Directories to exclude')
    parser.add_argument('--json', dest='json_output', help='JSON output file')
    parser.add_argument('--html', dest='html_output', help='HTML output file')
    parser.add_argument('--console', action='store_true', default=True, help='Print console report')
    parser.add_argument('--config', help='Config file (JSON)')
    
    args = parser.parse_args()
    
    # Load config if provided
    if args.config:
        with open(args.config, 'r', encoding='utf-8') as f:
            config = json.load(f)
        if not args.exclude_dirs and 'exclude_dirs' in config:
            args.exclude_dirs = config['exclude_dirs']
    
    # Create checker and run
    checker = CodeHealthChecker(
        root_dir=args.root_dir,
        file_threshold=args.file_threshold,
        function_threshold=args.function_threshold,
        exclude_dirs=args.exclude_dirs
    )
    
    print(f"Scanning project: {args.root_dir}")
    print(f"  File threshold: {args.file_threshold} lines")
    print(f"  Function threshold: {args.function_threshold} lines\n")
    
    checker.scan()
    
    # Generate reports
    if args.console:
        checker.generate_console_report()
    
    if args.json_output:
        checker.generate_json_report(args.json_output)
    
    if args.html_output:
        checker.generate_html_report(args.html_output)
    
    return 1 if checker.issues else 0


if __name__ == '__main__':
    sys.exit(main())
