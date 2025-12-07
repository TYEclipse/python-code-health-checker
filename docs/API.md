# API 文档

本文档详细说明了 Python Code Health Checker 的API，供希望将其集成到自己的项目中的开发者使用。

## 导入

```python
from src.code_health_checker import (
    CodeHealthChecker,
    CodeLineCounter,
    FunctionExtractor,
    FileIssue,
    FunctionIssue
)
```

## 核心类

### CodeHealthChecker

主控制类，用于扫描项目并生成报告。

#### 初始化

```python
checker = CodeHealthChecker(
    root_dir: str,
    file_threshold: int = 500,
    function_threshold: int = 50,
    exclude_dirs: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None
)
```

**参数**：

| 参数 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `root_dir` | `str` | 必需 | 要扫描的项目根目录 |
| `file_threshold` | `int` | 500 | 文件有效行数阈值 |
| `function_threshold` | `int` | 50 | 函数有效行数阈值 |
| `exclude_dirs` | `List[str]` | None | 要排除的目录列表 |
| `exclude_patterns` | `List[str]` | None | 要排除的文件模式列表（正则表达式） |

#### 方法

##### scan()

扫描项目目录，识别超标的文件和函数。

```python
checker.scan()
```

**返回值**：无。结果存储在 `checker.issues` 属性中。

**示例**：

```python
checker = CodeHealthChecker('/path/to/project')
checker.scan()
print(f"Found {len(checker.issues)} issues")
```

##### should_exclude(file_path)

判断指定的文件是否应被排除。

```python
is_excluded = checker.should_exclude(Path('/path/to/file.py'))
```

**参数**：

| 参数 | 类型 | 说明 |
| :--- | :--- | :--- |
| `file_path` | `Path` | 文件路径 |

**返回值**：`bool` - 如果应被排除则返回 `True`

##### generate_console_report()

生成并打印控制台格式的报告。

```python
checker.generate_console_report()
```

**示例输出**：

```
================================================================================
                        Python Code Health Check Report
================================================================================

Summary
--------------------------------------------------------------------------------
  Total issues: 1
  Files exceeding threshold: 1
  ...
```

##### generate_json_report(output_file)

生成JSON格式的报告文件。

```python
checker.generate_json_report('report.json')
```

**参数**：

| 参数 | 类型 | 说明 |
| :--- | :--- | :--- |
| `output_file` | `str` | 输出文件路径 |

**返回值**：无。生成的JSON文件包含以下结构：

```json
{
  "summary": {
    "total_issues": int,
    "files_exceeding_threshold": int,
    "functions_exceeding_threshold": int,
    "file_threshold": int,
    "function_threshold": int
  },
  "issues": [
    {
      "file_path": str,
      "total_lines": int,
      "effective_lines": int,
      "functions": [
        {
          "name": str,
          "start_line": int,
          "end_line": int,
          "effective_lines": int,
          "type": str  // "function" or "method"
        }
      ]
    }
  ]
}
```

##### generate_html_report(output_file)

生成HTML格式的交互式报告。

```python
checker.generate_html_report('report.html')
```

**参数**：

| 参数 | 类型 | 说明 |
| :--- | :--- | :--- |
| `output_file` | `str` | 输出文件路径 |

**返回值**：无。生成的HTML文件可直接在浏览器中打开。

### CodeLineCounter

用于计算代码的有效行数。

#### 初始化

```python
counter = CodeLineCounter(
    source_code: str,
    file_path: str = ""
)
```

**参数**：

| 参数 | 类型 | 说明 |
| :--- | :--- | :--- |
| `source_code` | `str` | Python源代码字符串 |
| `file_path` | `str` | 文件路径（用于调试） |

#### 方法

##### count_effective_lines(start_line, end_line)

计算指定范围内的有效行数。

```python
effective_count = counter.count_effective_lines(0, 50)
```

**参数**：

| 参数 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `start_line` | `int` | 0 | 起始行号（0-indexed） |
| `end_line` | `int` | None | 结束行号（0-indexed），None表示到文件末尾 |

**返回值**：`int` - 有效行数

**示例**：

```python
source = """
def hello():
    '''This is a docstring'''
    x = 1
    y = 2
    return x + y
"""

counter = CodeLineCounter(source)
effective = counter.count_effective_lines()
print(f"Effective lines: {effective}")  # 输出: Effective lines: 4
```

### FunctionExtractor

用于从Python代码中提取函数和方法信息。

#### 初始化

```python
extractor = FunctionExtractor(source_code: str)
```

**参数**：

| 参数 | 类型 | 说明 |
| :--- | :--- | :--- |
| `source_code` | `str` | Python源代码字符串 |

#### 属性

##### functions

提取的函数列表。

```python
functions = extractor.functions
```

**返回值**：`List[Dict]` - 函数信息列表，每个字典包含：

```python
{
    'name': str,           # 函数名
    'type': str,           # 'function' 或 'method'
    'class': str,          # 所属类名（如果是方法）
    'start_line': int,     # 起始行号
    'end_line': int,       # 结束行号
    'effective_lines': int # 有效行数
}
```

#### 方法

##### visit(tree)

访问AST树并提取函数信息。

```python
import ast
tree = ast.parse(source_code)
extractor.visit(tree)
```

**参数**：

| 参数 | 类型 | 说明 |
| :--- | :--- | :--- |
| `tree` | `ast.AST` | AST树 |

**返回值**：无。结果存储在 `functions` 属性中。

## 数据类

### FileIssue

表示超标的文件。

```python
@dataclass
class FileIssue:
    file_path: str                          # 文件路径
    total_lines: int                        # 总行数
    effective_lines: int                    # 有效行数
    functions: List[FunctionIssue] = []     # 超标函数列表
```

### FunctionIssue

表示超标的函数。

```python
@dataclass
class FunctionIssue:
    name: str                   # 函数名
    start_line: int             # 起始行号
    end_line: int               # 结束行号
    effective_lines: int        # 有效行数
    type: str                   # 'function' 或 'method'
```

## 使用示例

### 基本使用

```python
from src.code_health_checker import CodeHealthChecker

# 创建检查器
checker = CodeHealthChecker(
    root_dir='/path/to/project',
    file_threshold=500,
    function_threshold=50
)

# 扫描项目
checker.scan()

# 生成报告
checker.generate_console_report()
checker.generate_json_report('report.json')
checker.generate_html_report('report.html')

# 访问结果
for issue in checker.issues:
    print(f"File: {issue.file_path}")
    print(f"  Total lines: {issue.total_lines}")
    print(f"  Effective lines: {issue.effective_lines}")
    for func in issue.functions:
        print(f"    Function: {func.name} ({func.effective_lines} lines)")
```

### 自定义排除规则

```python
checker = CodeHealthChecker(
    root_dir='/path/to/project',
    exclude_dirs=['tests', 'docs', 'examples'],
    exclude_patterns=[r'.*_pb2\.py$']  # 排除protobuf生成的文件
)
checker.scan()
```

### 编程方式使用

```python
from src.code_health_checker import CodeLineCounter, FunctionExtractor

# 读取源代码
with open('my_module.py', 'r') as f:
    source = f.read()

# 计算有效行数
counter = CodeLineCounter(source)
total_effective = counter.count_effective_lines()
print(f"Total effective lines: {total_effective}")

# 提取函数信息
import ast
extractor = FunctionExtractor(source)
tree = ast.parse(source)
extractor.visit(tree)

for func in extractor.functions:
    if func['effective_lines'] > 50:
        print(f"Function {func['name']} has {func['effective_lines']} lines")
```

### 与CI/CD集成

```python
import sys
from src.code_health_checker import CodeHealthChecker

def main():
    checker = CodeHealthChecker(
        root_dir='.',
        file_threshold=500,
        function_threshold=50
    )
    
    checker.scan()
    checker.generate_html_report('report.html')
    
    if checker.issues:
        print(f"Found {len(checker.issues)} code quality issues")
        return 1  # 失败退出码
    
    print("All code quality checks passed!")
    return 0  # 成功退出码

if __name__ == '__main__':
    sys.exit(main())
```

## 常见问题

### Q: 如何修改有效行数的定义？

A: 修改 `CodeLineCounter._identify_docstrings()` 和 `count_effective_lines()` 方法中的逻辑。

### Q: 如何添加新的检查维度？

A: 创建新的检查器类，继承或参考 `CodeHealthChecker` 的设计模式。

### Q: 如何处理编码问题？

A: 在读取文件时指定编码，例如：

```python
with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
    source = f.read()
```

### Q: 性能如何？

A: 该工具的性能很好。对于典型的项目（数百个文件），扫描通常在几秒内完成。

## 许可证

MIT License

---

**版本**：1.0  
**最后更新**：2025年12月07日
