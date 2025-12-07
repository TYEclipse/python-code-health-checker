# 贡献指南

感谢您对 Python Code Health Checker 的兴趣！我们欢迎任何形式的贡献，包括bug报告、功能建议、文档改进和代码提交。

## 行为准则

本项目采用 Contributor Covenant 行为准则。参与本项目即表示您同意遵守该准则。如发现违反行为，请联系项目维护者。

## 如何贡献

### 报告Bug

在提交bug报告前，请先检查 Issues 列表，确保该问题尚未被报告。

提交bug报告时，请包含以下信息：

- **简明的标题和描述**
- **复现步骤**：尽可能详细地说明如何复现该问题
- **预期行为**：描述您期望发生的情况
- **实际行为**：描述实际发生的情况
- **您的环境**：包括操作系统、Python版本等
- **截图或日志**：如果适用

### 提出功能建议

功能建议也通过 Issues 提交。请提供以下信息：

- **清晰的标题和描述**
- **使用场景**：解释为什么需要这个功能
- **可能的实现方式**：如果有想法的话

### 提交代码

1. **Fork 仓库**：点击 GitHub 上的 Fork 按钮
2. **创建特性分支**：`git checkout -b feature/your-feature-name`
3. **进行更改**：编写代码并添加测试
4. **运行测试**：确保所有测试通过
5. **提交更改**：`git commit -am 'Add some feature'`
6. **推送到分支**：`git push origin feature/your-feature-name`
7. **提交 Pull Request**：描述您的更改内容

### 代码风格

- 遵循 PEP 8 风格指南
- 使用有意义的变量和函数名
- 为复杂逻辑添加注释
- 编写文档字符串（docstrings）

### 提交消息格式

使用清晰、简明的提交消息：

```
[类型] 简明描述

详细说明（如果需要）

Fixes #issue_number (如果适用)
```

类型包括：
- `feat`: 新功能
- `fix`: bug修复
- `docs`: 文档更新
- `style`: 代码风格改变（不影响功能）
- `refactor`: 代码重构
- `test`: 添加或修改测试
- `chore`: 构建过程、依赖管理等

## 开发环境设置

```bash
# 克隆仓库
git clone https://github.com/your-username/python-code-health-checker.git
cd python-code-health-checker

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装开发依赖
pip install -r requirements-dev.txt

# 运行测试
python -m pytest tests/

# 运行代码检查
python src/code_health_checker.py . --config config.json
```

## 测试

- 为新功能添加单元测试
- 确保所有测试通过：`python -m pytest tests/`
- 保持测试覆盖率在 80% 以上

## 文档

- 更新 README.md 以反映您的更改
- 为新功能添加文档
- 保持文档与代码同步

## 许可证

通过提交代码，您同意将您的贡献在 MIT License 下发布。

## 问题？

如有任何问题，请通过以下方式联系：

- 在 GitHub Issues 中提问
- 查看现有文档和讨论

感谢您的贡献！
