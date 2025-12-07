# Python Code Health Checker

一个专业的、生产级别的Python代码库结构健康度自动化检查工具。通过精确的AST解析，自动识别代码行数超标的文件和函数，并生成多种格式的详细报告。

## 特性

- **精确的有效代码行计算**：通过AST解析，准确排除空行、注释和文档字符串
- **灵活的阈值设置**：可自定义文件和函数的行数阈值
- **智能目录排除**：自动排除常见的非项目代码目录（.venv, .git等）
- **多格式输出**：支持控制台、JSON和HTML三种报告格式
- **零依赖**：仅使用Python标准库，无需安装第三方包
- **生产就绪**：经过充分测试，可直接用于CI/CD流程

## 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/your-username/python-code-health-checker.git
cd python-code-health-checker

# 无需安装依赖，脚本仅使用Python标准库
```

### 基本使用

```bash
# 扫描项目并打印控制台报告
python3 src/code_health_checker.py /path/to/your/project

# 生成完整报告
python3 src/code_health_checker.py /path/to/your/project \
  --json report.json \
  --html report.html \
  --exclude-dir tests \
  --exclude-dir examples

# 使用配置文件
python3 src/code_health_checker.py /path/to/your/project --config config.json
```

## 命令行参数

```
usage: code_health_checker.py [-h] [--file-threshold FILE_THRESHOLD]
                              [--function-threshold FUNCTION_THRESHOLD]
                              [--exclude-dir EXCLUDE_DIRS] [--json JSON_OUTPUT]
                              [--html HTML_OUTPUT] [--console] [--config CONFIG]
                              root_dir

positional arguments:
  root_dir              Project root directory

optional arguments:
  -h, --help            Show help message
  --file-threshold      File threshold in lines (default: 500)
  --function-threshold  Function threshold in lines (default: 50)
  --exclude-dir         Directories to exclude (can be used multiple times)
  --json                JSON output file path
  --html                HTML output file path
  --console             Print console report (default: true)
  --config              Config file path (JSON format)
```

## 配置文件示例

创建 `code_health_config.json`：

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
    "docs"
  ]
}
```

## 报告格式

### 控制台输出

```
================================================================================
                        Python Code Health Check Report
================================================================================

Summary
--------------------------------------------------------------------------------
  Total issues: 1
  Files exceeding threshold: 1
  Functions exceeding threshold: 1
  File threshold: 500 lines
  Function threshold: 50 lines

Issues Details
--------------------------------------------------------------------------------

1. src/oversized_module.py
   Total lines: 493, Effective lines: 290
   Functions exceeding threshold:
     - process_large_dataset (function)
       Lines: 21-99, Effective: 53

================================================================================
```

### JSON 格式

```json
{
  "summary": {
    "total_issues": 1,
    "files_exceeding_threshold": 1,
    "functions_exceeding_threshold": 1,
    "file_threshold": 500,
    "function_threshold": 50
  },
  "issues": [
    {
      "file_path": "src/oversized_module.py",
      "total_lines": 493,
      "effective_lines": 290,
      "functions": [
        {
          "name": "process_large_dataset",
          "start_line": 21,
          "end_line": 99,
          "effective_lines": 53,
          "type": "function"
        }
      ]
    }
  ]
}
```

### HTML 报告

生成的HTML报告是一个美观的、交互式的页面，可直接在浏览器中打开。

## CI/CD 集成

### GitHub Actions

在 `.github/workflows/code-health-check.yml` 中添加：

```yaml
name: Code Health Check

on: [push, pull_request]

jobs:
  code-health-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Run Code Health Check
        run: |
          python3 src/code_health_checker.py . --config config.json --html report.html
      
      - name: Upload Report
        uses: actions/upload-artifact@v3
        if: failure()
        with:
          name: code-health-report
          path: report.html
```

## 项目结构

```
python-code-health-checker/
├── src/
│   └── code_health_checker.py      # 主检查脚本
├── tests/
│   └── test_code_health_checker.py # 单元测试
├── examples/
│   └── sample_project/             # 示例项目
├── docs/
│   ├── DESIGN.md                   # 设计文档
│   ├── API.md                      # API文档
│   └── USAGE.md                    # 使用指南
├── .github/
│   └── workflows/
│       └── code-health-check.yml   # GitHub Actions工作流
├── config.json                     # 配置文件示例
├── README.md                       # 项目说明
├── LICENSE                         # 许可证
└── CONTRIBUTING.md                 # 贡献指南
```

## 最佳实践

1. **配置文件管理**：在项目根目录维护一个 `code_health_config.json` 文件，确保团队成员使用一致的检查标准。

2. **定期检查**：将脚本集成到CI/CD流程中，在每次代码提交或合并时自动运行。

3. **渐进式改进**：如果发现大量超标代码，可以逐步提高阈值，而不是一次性要求所有代码都符合标准。

4. **团队讨论**：定期审查报告，与团队讨论代码复杂度问题，制定改进计划。

## 技术细节

### 有效代码行定义

有效代码行（Effective Lines of Code, ELOC）是指在程序执行中贡献实际逻辑的代码行。计算时会排除：

- **空行**：完全不包含任何字符或仅包含空白字符的行
- **注释**：以 `#` 开头的单行注释
- **文档字符串**：作为模块、函数、类或方法的第一个语句的字符串字面量

### 实现原理

该工具使用Python的 `ast` 模块来解析代码的抽象语法树（AST），从而精确地：

1. 识别所有函数和方法定义
2. 定位文档字符串的位置
3. 计算每个代码块的有效行数
4. 与预设阈值进行比较

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 贡献

欢迎提交Issue和Pull Request！详见 [CONTRIBUTING.md](CONTRIBUTING.md)

## 作者

**Manus AI** - 开发工程师与代码质量顾问

## 相关资源

- [设计文档](docs/DESIGN.md) - 详细的技术设计和架构说明
- [API文档](docs/API.md) - 脚本的API和扩展指南
- [使用指南](docs/USAGE.md) - 详细的使用说明和示例

---

**版本**：1.0  
**最后更新**：2025年12月07日
