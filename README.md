# Report Killer

一个智能的文档填写助手，使用 AI 自动理解并填写 Word 文档中的问题和空白。

## 功能特性

- 📝 **自动理解文档**：智能解析 Word 文档内容，识别问题和需要填写的位置
- 🤖 **AI 驱动**：使用先进的 AI 模型（支持 OpenAI 兼容 API）生成高质量答案
- 🎯 **精确插入**：在正确的位置插入答案，而不是简单追加到文档末尾
- ⚙️ **灵活配置**：支持自定义 API、模型、代理和提示词
- 🔒 **保护原文**：不修改文档中的问题和标题，只填写答案

## 安装

### 环境要求

- Python 3.10 或更高版本
- 网络连接（用于调用 AI API）

### 使用 pip 安装

```bash
# 克隆仓库
git clone https://github.com/HeavySnowJakarta/report-killer.git
cd report-killer

# 安装依赖
pip install -e .
```

### 使用 uv 安装（推荐）

```bash
# 克隆仓库
git clone https://github.com/HeavySnowJakarta/report-killer.git
cd report-killer

# 使用 uv 安装
uv pip install -e .
```

## 快速开始

### 1. 配置

首次使用前，需要配置 API 密钥和其他设置：

```bash
report-killer configure
```

系统会提示你输入：
- **API URL**：OpenAI 兼容 API 的地址（默认：https://openrouter.ai/api/v1）
- **API Key**：你的 API 密钥
- **Model**：要使用的模型（默认：anthropic/claude-3.5-sonnet）
- **代理设置**（可选）：HTTP/HTTPS 代理
- **自定义提示词**（可选）：对 AI 输出的额外要求

### 2. 处理文档

```bash
# 处理文档（会覆盖原文件）
report-killer process path/to/your/document.docx

# 指定输出文件
report-killer process input.docx -o output.docx

# 使用自定义提示词
report-killer process input.docx --prompt "输出内容要简洁，不超过100字"
```

### 3. 测试

使用项目提供的测试文档进行测试：

```bash
report-killer test
```

测试结果会保存到 `documents/test_ai_doc_output.docx`。

### 4. 查看配置

```bash
report-killer info
```

## 使用示例

### 配置文件

配置信息保存在项目根目录的 `config.json` 文件中：

```json
{
  "api_url": "https://openrouter.ai/api/v1",
  "api_key": "your-api-key-here",
  "model": "anthropic/claude-3.5-sonnet",
  "http_proxy": null,
  "https_proxy": null,
  "custom_prompt": "输出内容不得包含加粗文本、标题及无序列表",
  "documents_dir": "documents"
}
```

你也可以直接编辑这个文件，或使用环境变量：

```bash
export OPENAI_API_KEY="your-api-key"
export OPENAI_API_URL="https://api.openai.com/v1"
export OPENAI_MODEL="gpt-4"
export HTTP_PROXY="http://proxy.example.com:8080"
export HTTPS_PROXY="https://proxy.example.com:8080"
```

### 工作流程

1. **文档分析**：程序读取 Word 文档，识别问题、空白和文档结构
2. **AI 处理**：将文档内容发送给 AI，让它理解问题并生成答案
3. **精确插入**：将答案插入到正确的位置（问题之后，而非文档末尾）
4. **保存结果**：保存修改后的文档

## 注意事项

### 文档兼容性

- 支持标准的 .docx 格式文档
- 如果遇到文档格式错误，请尝试用 Microsoft Word 或 LibreOffice 重新保存文档

### API 使用

- 本工具使用 OpenAI 兼容的 API
- 支持 OpenRouter、OpenAI、Claude API 等
- 请注意 API 调用会产生费用，建议设置合理的预算

### 文件管理

- `documents/` 目录用于存储输入输出文档（已加入 .gitignore）
- `config.json` 包含敏感信息（已加入 .gitignore）
- 不要将 API 密钥提交到版本控制系统

## 高级用法

### 自定义提示词

通过自定义提示词，你可以控制 AI 的输出风格：

```bash
# 要求简洁的答案
report-killer process doc.docx --prompt "回答要简洁明了，每个问题不超过50字"

# 要求详细的答案
report-killer process doc.docx --prompt "提供详细的分析和解释，包含具体的例子"

# 控制格式
report-killer process doc.docx --prompt "不使用 Markdown 格式，不使用加粗或斜体"
```

### 批量处理

```bash
# 使用 shell 循环批量处理
for file in documents/*.docx; do
    report-killer process "$file" -o "documents/processed_$(basename $file)"
done
```

## 开发

### 项目结构

```
report-killer/
├── report_killer/          # 主要代码
│   ├── __init__.py
│   ├── cli.py             # 命令行界面
│   ├── config.py          # 配置管理
│   ├── agent.py           # AI 代理
│   └── docx_handler.py    # Word 文档处理
├── tests/                 # 测试文件
│   └── test_ai_doc.docx
├── documents/             # 文档存储目录（.gitignore）
├── pyproject.toml         # 项目配置
└── README.md
```

### 运行测试

```bash
# 运行内置测试
report-killer test
```

## 故障排除

### 问题：无法加载文档

```
Error loading document: Document has incompatible format
```

**解决方案**：用 Microsoft Word 或 LibreOffice 打开文档并另存为新的 .docx 文件。

### 问题：API 调用失败

```
Error calling AI API: ...
```

**解决方案**：
1. 检查 API 密钥是否正确
2. 检查网络连接
3. 如果在中国大陆，检查代理设置
4. 验证 API URL 是否正确

### 问题：答案位置不正确

**解决方案**：这可能是文档结构复杂导致的。尝试：
1. 简化文档结构
2. 确保问题明确（以问号结尾）
3. 使用更具体的自定义提示词

## 许可证

本项目使用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 贡献

欢迎提交 Issue 和 Pull Request！

## 致谢

- 使用 [python-docx](https://python-docx.readthedocs.io/) 处理 Word 文档
- 使用 [Anthropic](https://www.anthropic.com/) 的 Claude API
- 使用 [Click](https://click.palletsprojects.com/) 构建命令行界面
- 使用 [Rich](https://rich.readthedocs.io/) 提供美观的终端输出
