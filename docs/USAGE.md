# 使用指南

本指南将帮助您快速上手 Python Code Health Checker，并展示如何在不同场景中使用它。

## 目录

1. [安装](#安装)
2. [基本使用](#基本使用)
3. [命令行参数](#命令行参数)
4. [配置文件](#配置文件)
5. [输出格式](#输出格式)
6. [常见场景](#常见场景)
7. [最佳实践](#最佳实践)
8. [故障排除](#故障排除)

## 安装

### 要求

- Python 3.8 或更高版本
- 无需安装任何第三方依赖

### 获取脚本

```bash
# 克隆仓库
git clone https://github.com/your-username/python-code-health-checker.git
cd python-code-health-checker

# 或者直接下载脚本
wget https://raw.githubusercontent.com/your-username/python-code-health-checker/main/src/code_health_checker.py
```

## 基本使用

### 最简单的使用方式

```bash
# 扫描当前目录
python3 src/code_health_checker.py .

# 扫描指定目录
python3 src/code_health_checker.py /path/to/your/project
```

### 查看帮助

```bash
python3 src/code_health_checker.py --help
```

## 命令行参数

### 位置参数

```
root_dir              要扫描的项目根目录（必需）
```

### 可选参数

| 参数 | 说明 | 默认值 | 示例 |
| :--- | :--- | :--- | :--- |
| `--file-threshold` | 文件有效行数阈值 | 500 | `--file-threshold 400` |
| `--function-threshold` | 函数有效行数阈值 | 50 | `--function-threshold 40` |
| `--exclude-dir` | 排除的目录（可多次使用） | 无 | `--exclude-dir tests --exclude-dir docs` |
| `--json` | JSON报告输出路径 | 无 | `--json report.json` |
| `--html` | HTML报告输出路径 | 无 | `--html report.html` |
| `--console` | 打印控制台报告 | true | `--console` |
| `--config` | 配置文件路径 | 无 | `--config config.json` |
| `-h, --help` | 显示帮助信息 | 无 | `--help` |

## 配置文件

### 创建配置文件

在项目根目录创建 `code_health_config.json`：

```json
{
  "file_threshold": 500,
  "function_threshold": 50,
  "exclude_dirs": [
    "__pycache__",
    ".git",
    ".venv",
    "venv",
    "env",
    "node_modules",
    ".pytest_cache",
    ".tox",
    "dist",
    "build",
    ".mypy_cache",
    ".coverage",
    "tests",
    "docs",
    "examples"
  ],
  "description": "项目的代码健康度检查配置"
}
```

### 使用配置文件

```bash
python3 src/code_health_checker.py . --config code_health_config.json
```

### 配置文件优先级

命令行参数 > 配置文件 > 默认值

## 输出格式

### 控制台输出

默认输出格式，包含摘要和详细问题列表：

```
================================================================================
                        Python Code Health Check Report
================================================================================

Summary
--------------------------------------------------------------------------------
  Total issues: 2
  Files exceeding threshold: 2
  Functions exceeding threshold: 3
  File threshold: 500 lines
  Function threshold: 50 lines

Issues Details
--------------------------------------------------------------------------------

1. src/module1.py
   Total lines: 600, Effective lines: 550
   WARNING: File exceeds threshold: 550 > 500
   Functions exceeding threshold:
     - process_data (function)
       Lines: 10-80, Effective: 60

2. src/module2.py
   Total lines: 700, Effective lines: 620
   WARNING: File exceeds threshold: 620 > 500
   Functions exceeding threshold:
     - analyze_results (function)
       Lines: 50-120, Effective: 55
     - generate_report (function)
       Lines: 150-220, Effective: 65

================================================================================
```

### JSON输出

机器可读的JSON格式，便于自动化处理：

```bash
python3 src/code_health_checker.py . --json report.json
```

生成的 `report.json` 结构：

```json
{
  "summary": {
    "total_issues": 2,
    "files_exceeding_threshold": 2,
    "functions_exceeding_threshold": 3,
    "file_threshold": 500,
    "function_threshold": 50
  },
  "issues": [
    {
      "file_path": "src/module1.py",
      "total_lines": 600,
      "effective_lines": 550,
      "functions": [
        {
          "name": "process_data",
          "start_line": 10,
          "end_line": 80,
          "effective_lines": 60,
          "type": "function"
        }
      ]
    }
  ]
}
```

### HTML输出

美观的交互式报告，可直接在浏览器中打开：

```bash
python3 src/code_health_checker.py . --html report.html
```

然后在浏览器中打开 `report.html`。

## 常见场景

### 场景1：检查整个项目

```bash
python3 src/code_health_checker.py /path/to/project \
  --file-threshold 500 \
  --function-threshold 50 \
  --exclude-dir tests \
  --exclude-dir docs \
  --html report.html
```

### 场景2：严格检查（降低阈值）

```bash
python3 src/code_health_checker.py /path/to/project \
  --file-threshold 300 \
  --function-threshold 30 \
  --json strict_report.json
```

### 场景3：宽松检查（提高阈值）

```bash
python3 src/code_health_checker.py /path/to/project \
  --file-threshold 1000 \
  --function-threshold 100
```

### 场景4：只检查特定目录

```bash
python3 src/code_health_checker.py /path/to/project/src \
  --exclude-dir tests \
  --exclude-dir __pycache__
```

### 场景5：生成所有格式的报告

```bash
python3 src/code_health_checker.py /path/to/project \
  --config code_health_config.json \
  --json report.json \
  --html report.html \
  --console
```

### 场景6：CI/CD集成

```bash
#!/bin/bash
python3 src/code_health_checker.py . \
  --config code_health_config.json \
  --html report.html

if [ $? -ne 0 ]; then
  echo "Code health check failed!"
  exit 1
fi

echo "Code health check passed!"
exit 0
```

## 最佳实践

### 1. 使用配置文件

在项目根目录维护 `code_health_config.json`，确保团队成员使用一致的标准：

```bash
python3 src/code_health_checker.py . --config code_health_config.json
```

### 2. 定期检查

将检查集成到CI/CD流程中，在每次代码提交时自动运行。

### 3. 渐进式改进

如果发现大量超标代码，不要一次性要求所有代码都符合标准。相反，应该：

1. 记录当前的超标项
2. 制定改进计划
3. 逐步提高代码质量
4. 定期审查进度

### 4. 团队讨论

定期审查报告，与团队讨论：

- 哪些文件/函数最需要重构
- 是否需要调整阈值
- 如何改进代码结构

### 5. 排除非项目代码

确保排除了所有非项目代码：

```json
{
  "exclude_dirs": [
    "tests",
    "docs",
    "examples",
    ".venv",
    "venv",
    "build",
    "dist"
  ]
}
```

### 6. 版本控制

将配置文件纳入版本控制，以便团队共享：

```bash
git add code_health_config.json
git commit -m "Add code health check configuration"
```

## 故障排除

### 问题1：找不到Python文件

**症状**：报告显示 "No code quality issues found!" 但您知道有Python文件存在。

**解决方案**：
1. 检查路径是否正确
2. 确认目录中确实有 `.py` 文件
3. 检查是否被排除规则过滤了

```bash
# 查看目录结构
find /path/to/project -name "*.py" | head -20
```

### 问题2：某些文件被错误排除

**症状**：某个重要文件没有出现在报告中。

**解决方案**：
1. 检查排除规则
2. 验证文件路径是否匹配排除模式

```bash
# 调试排除规则
python3 -c "
from pathlib import Path
from src.code_health_checker import CodeHealthChecker

checker = CodeHealthChecker('.')
file_path = Path('path/to/file.py')
print(f'Should exclude: {checker.should_exclude(file_path)}')
"
```

### 问题3：编码错误

**症状**：出现 `UnicodeDecodeError` 错误。

**解决方案**：脚本已配置为忽略编码错误，如果仍有问题，检查文件编码：

```bash
# 检查文件编码
file -i /path/to/file.py
```

### 问题4：语法错误

**症状**：某个Python文件被跳过。

**解决方案**：脚本会跳过有语法错误的文件。修复语法错误后重新运行：

```bash
# 检查语法
python3 -m py_compile /path/to/file.py
```

### 问题5：性能问题

**症状**：扫描大型项目时很慢。

**解决方案**：
1. 排除不必要的目录
2. 使用更具体的路径

```bash
# 只扫描src目录
python3 src/code_health_checker.py ./src --exclude-dir tests
```

## 获取帮助

- 查看本文档的其他部分
- 查看 [API文档](API.md)
- 查看 [设计文档](DESIGN.md)
- 在GitHub上提交Issue

---

**版本**：1.0  
**最后更新**：2025年12月07日
