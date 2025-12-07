#!/usr/bin/env python3
"""
Python Code Health Checker

Analyzes Python projects to identify files and functions exceeding specified
line count thresholds. Generates reports in multiple formats (console, JSON, HTML).
"""

import ast
import json
import re
import sys
import html
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import List, Optional, Set


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

    def __init__(self, source_code: str):
        # 保留 source_code 用于后续解析；file_path 参数在类内部未使用，删除以简化接口
        self.source_code = source_code
        self.lines = source_code.splitlines()
        self.docstring_ranges: Set[int] = set()
        self._identify_docstrings()

    def _identify_docstrings(self) -> None:
        """Identify all docstring line ranges using AST (robust across Python versions)."""
        try:
            tree = ast.parse(self.source_code)
        except SyntaxError:
            return

        # 使用 ast.get_docstring 来稳健判断模块/类/函数的 docstring
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue

            # 确保节点有 body 并且第一个语句是表达式（可能是 docstring）
            if not getattr(node, "body", None):
                continue

            first_stmt = node.body[0]
            if not isinstance(first_stmt, ast.Expr):
                continue

            # 利用 ast.get_docstring 以兼容 ast.Constant / ast.Str 等不同表示
            docstring = ast.get_docstring(node, clean=False)
            if docstring is None:
                continue

            if hasattr(first_stmt, "lineno"):
                start = first_stmt.lineno - 1
                # 若 AST 提供 end_lineno，直接使用；否则根据 docstring 文本估算行数
                if hasattr(first_stmt, "end_lineno") and first_stmt.end_lineno is not None:
                    end = first_stmt.end_lineno
                else:
                    # docstring 中换行数 + 起始行（注意：end 是 1-indexed）
                    end = start + docstring.count("\n") + 1

                # 限制在文件行数范围内并记录索引（0-indexed）
                for i in range(start, min(end, len(self.lines))):
                    self.docstring_ranges.add(i)

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

    def _process_function(self, node: ast.AST) -> None:
        # 使用更通用的 AST 类型注释，兼容 FunctionDef / AsyncFunctionDef
        start_line = node.lineno - 1
        end_line = getattr(node, 'end_lineno', None)
        if end_line is None:
            # 最小化风险：若 node 没有 end_lineno，尝试用 body 最后一项的 lineno
            if getattr(node, 'body', None):
                last = node.body[-1]
                end_line = getattr(last, 'end_lineno', getattr(
                    last, 'lineno', start_line + 1))
            else:
                end_line = start_line + 1

        effective_lines = self.counter.count_effective_lines(
            start_line, end_line)
        func_type = 'method' if self.current_class else 'function'

        self.functions.append({
            'name': getattr(node, 'name', '<lambda>'),
            'type': func_type,
            'class': self.current_class,
            'start_line': getattr(node, 'lineno', start_line + 1),
            'end_line': end_line,
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
        # 检查路径各级与用户配置目录精确匹配
        for exclude_dir in self.exclude_dirs:
            if exclude_dir in file_path.parts:
                return True

        file_str = str(file_path)
        # 使用 search 以便匹配路径中任意位置的模式
        for pattern in self.exclude_patterns:
            try:
                if re.search(pattern, file_str):
                    return True
            except re.error:
                # 忽略错误的正则模式，避免整个扫描失败
                continue

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
                print(
                    f"Warning: Error processing {file_path}: {e}", file=sys.stderr)

    def _check_file(self, file_path: Path) -> None:
        """Check a single Python file."""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            source_code = f.read()

        counter = CodeLineCounter(source_code)
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

    def _build_html_header(self) -> List[str]:
        """
        构建 HTML 文件的头部与通用样式。
        返回值:
          List[str] - 按行组成的 HTML 头部内容（到 <div class="content"> 开始之前）。
        用途:
          将样式与页面元信息集中在一个函数，便于后续修改样式或国际化。
        """
        # 使用局部变量 html_lines 保存每一行，便于逐行拼接与单元测试
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
        ]
        return html_lines

    def _build_summary_section(self, html_lines: List[str]) -> None:
        """
        将摘要卡片追加到 html_lines。
        输入:
          html_lines - 当前的 html 行列表（会在函数内被修改/追加）。
        摘要内容包括：
          - 总问题数 (len(self.issues))
          - 超标文件数 (len(self.issues))
          - 超标函数数 (sum of lengths)
          - 文件阈值和函数阈值
        """
        # 统计数据（可单独测试）
        total_issues = len(self.issues)
        files_exceeding = len(self.issues)
        functions_exceeding = sum(len(issue.functions)
                                  for issue in self.issues)

        # 将摘要卡片按行追加
        html_lines.extend([
            f'            <div class="summary-card"><h3>Total Issues</h3><div class="value">{total_issues}</div></div>',
            f'            <div class="summary-card"><h3>Files Exceeding</h3><div class="value">{files_exceeding}</div></div>',
            f'            <div class="summary-card"><h3>Functions Exceeding</h3><div class="value">{functions_exceeding}</div></div>',
            f'            <div class="summary-card"><h3>File Threshold</h3><div class="value">{self.file_threshold}</div></div>',
            f'            <div class="summary-card"><h3>Function Threshold</h3><div class="value">{self.function_threshold}</div></div>',
            '        </div>',  # 关闭 summary
            '        <div class="content">',
        ])

    def _build_issues_section(self, html_lines: List[str]) -> None:
        """
        将 issues 的展示内容追加到 html_lines。
        逻辑:
          - 若 self.issues 为空，追加一段提示信息；
          - 否则循环每个 issue，构建文件区块(file-section)，并在 file-details 中展示文件超标信息与函数表格。
        注：函数与 issue 的字段说明
          issue.file_path: 相对于 root 的路径字符串
          issue.total_lines: 文件总行数
          issue.effective_lines: 有效行数（不含注释/空行/文档字符串）
          issue.functions: List[FunctionIssue]（每个包含 name/type/start_line/end_line/effective_lines）
        """
        # 无问题时显示占位信息
        if not self.issues:
            html_lines.append(
                '            <div class="no-issues">No code quality issues found!</div>')
            return

        # 有问题时为每个 issue 生成区块
        for issue in self.issues:
            # 文件路径/函数名在 HTML 中做转义，避免注入或特殊字符破坏页面
            safe_path = html.escape(issue.file_path)
            html_lines.append(f'            <div class="file-section">')
            html_lines.append(
                f'                <div class="file-header" onclick="this.nextElementSibling.classList.toggle(\'show\')">')
            html_lines.append(
                f'                    <span><strong>{safe_path}</strong> ({issue.effective_lines}/{issue.total_lines} lines)</span>')
            html_lines.append(f'                    <span>▼</span>')
            html_lines.append(f'                </div>')

            html_lines.append(
                f'                <div class="file-details show">')

            if issue.effective_lines > self.file_threshold:
                html_lines.append(
                    f'                    <p><span class="warning">File exceeds threshold: {issue.effective_lines} > {self.file_threshold}</span></p>')

            if issue.functions:
                html_lines.append('                    <table>')
                html_lines.append(
                    '                        <thead><tr><th>Function</th><th>Type</th><th>Lines</th><th>Effective Lines</th></tr></thead>')
                html_lines.append('                        <tbody>')
                for func in issue.functions:
                    safe_name = html.escape(func.name)
                    safe_type = html.escape(func.type)
                    html_lines.append(
                        f'                            <tr><td>{safe_name}</td><td>{safe_type}</td><td>{func.start_line}-{func.end_line}</td><td><span class="warning">{func.effective_lines}</span></td></tr>')
                html_lines.append('                        </tbody>')
                html_lines.append('                    </table>')

            html_lines.append('                </div>')
            html_lines.append('            </div>')

    def _write_html_file(self, output_file: str, html_lines: List[str]) -> None:
        """
        将 html_lines 写入指定文件。
        输入:
          output_file - 目标文件路径
          html_lines - 按行的 HTML 内容
        该函数抽离 IO 操作，便于在单元测试中替换/模拟文件写入。
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(html_lines))
        # 向用户反馈写入结果（保持原有行为）
        print(f"HTML report generated: {output_file}")

    def generate_html_report(self, output_file: str) -> None:
        """
        生成 HTML 报告的主调度函数（入口）。
        职责:
          - 协调各个子步骤：头部构建 -> 摘要 -> issues -> 写入文件。
        输入:
          output_file: 输出 HTML 文件路径（字符串）
        输出:
          无返回值；将 HTML 写入磁盘并打印生成路径。
        实现要点:
          - 将每个逻辑单元委派给私有函数，保证单一职责和可测试性；
          - 对每个中间结构（如 html_lines）添加注释，便于调试。
        """
        # 1) 构建头部与基础结构（返回 List[str]）
        html_lines = self._build_html_header()

        # 2) 拼接摘要区域（直接在 html_lines 上追加）
        self._build_summary_section(html_lines)

        # 3) 拼接 issues 内容区域（含具体文件/函数表格）
        self._build_issues_section(html_lines)

        # 4) 追加尾部闭合标签
        html_lines.extend([
            '        </div>',  # 关闭 content
            '    </div>',      # 关闭 container
            '</body>',
            '</html>'
        ])

        # 5) 将构建好的 HTML 写入文件（抽离为独立函数以便测试）
        self._write_html_file(output_file, html_lines)

    def generate_console_report(self) -> None:
        """Generate console format report."""
        print("\n" + "="*80)
        print("Python Code Health Check Report".center(80))
        print("="*80 + "\n")

        print("Summary")
        print("-" * 80)
        print(f"  Total issues: {len(self.issues)}")
        print(f"  Files exceeding threshold: {len(self.issues)}")
        print(
            f"  Functions exceeding threshold: {sum(len(issue.functions) for issue in self.issues)}")
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
            print(
                f"   Total lines: {issue.total_lines}, Effective lines: {issue.effective_lines}")

            if issue.effective_lines > self.file_threshold:
                print(
                    f"   WARNING: File exceeds threshold: {issue.effective_lines} > {self.file_threshold}")

            if issue.functions:
                print(f"   Functions exceeding threshold:")
                for func in issue.functions:
                    print(f"     - {func.name} ({func.type})")
                    print(
                        f"       Lines: {func.start_line}-{func.end_line}, Effective: {func.effective_lines}")

        print("\n" + "="*80 + "\n")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Python Code Health Checker',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('root_dir', help='Project root directory')
    parser.add_argument('--file-threshold', type=int,
                        default=500, help='File threshold (default: 500)')
    parser.add_argument('--function-threshold', type=int,
                        default=50, help='Function threshold (default: 50)')
    parser.add_argument('--exclude-dir', action='append',
                        dest='exclude_dirs', help='Directories to exclude')

    # 改为 --no-console 控制选项，默认打印控制台，用户可通过 --no-console 关闭
    parser.add_argument('--no-console', action='store_false', dest='console',
                        default=True, help='Disable console report')

    parser.add_argument('--json', dest='json_output', help='JSON output file')
    parser.add_argument('--html', dest='html_output', help='HTML output file')
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
