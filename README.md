# Report Killer

一个智能的文档填写助手，使用 AI 自动理解并填写 Word 文档中的问题和空白。

## 🚀 主要特性

- **📝 自动理解文档**：智能解析 Word 文档内容，识别问题和需要填写的位置
- **🤖 AI 驱动**：使用先进的 AI 模型生成高质量答案
- **🎯 精确插入**：在正确的位置插入答案，保护原文档结构
- **🔄 代码执行重试**：自动重试失败的代码，AI 智能修复语法错误
- **📊 专业表格**：Markdown 表格自动转换为 Word 表格格式
- **🧹 清洁输出**：文档中只插入内容，错误信息显示在终端
- **⚙️ 灵活配置**：支持多种 AI 服务、自定义提示词和代理设置

## 📋 环境要求

- Python 3.10 或更高版本
- 网络连接（用于调用 AI API）
- 有效的 OpenAI 兼容 API 密钥

## 🛠 安装

### 方法 1：使用 pip

```bash
# 克隆仓库
git clone https://github.com/HeavySnowJakarta/report-killer.git
cd report-killer

# 安装依赖
pip install -e .
```

### 方法 2：使用 uv（推荐）

```bash
# 克隆仓库
git clone https://github.com/HeavySnowJakarta/report-killer.git
cd report-killer

# 使用 uv 安装
uv pip install -e .
```

## 🔧 配置

### 1. 获取 API 密钥

选择以下服务之一：

**OpenRouter（推荐用于测试）**
- 访问 [OpenRouter](https://openrouter.ai/)
- 注册账号，创建 API 密钥
- 充值少量余额（$1-5 用于测试）

**OpenAI**
- 访问 [OpenAI Platform](https://platform.openai.com/)
- 注册账号并绑定支付方式
- 创建 API 密钥

**其他服务**
- Claude API（Anthropic）
- 本地 LLM 服务（LM Studio、Ollama 等）

### 2. 配置设置

```bash
report-killer configure
```

系统会提示输入：
- **API URL**：API 端点地址（默认：https://openrouter.ai/api/v1）
- **API Key**：你的 API 密钥
- **Model**：使用的模型（默认：anthropic/claude-3.5-sonnet）
- **代理设置**（可选）：HTTP/HTTPS 代理
- **自定义提示词**（可选）：控制 AI 输出风格
- **文档目录**：文档存储位置（默认：documents）

### 3. 配置文件示例

配置保存在 `config.json`：

```json
{
  "api_url": "https://openrouter.ai/api/v1",
  "api_key": "your-api-key-here",
  "model": "anthropic/claude-3.5-sonnet",
  "http_proxy": null,
  "https_proxy": null,
  "custom_prompt": "输出内容不得包含加粗文本、标题及无序列表",
  "documents_dir": "documents",
  "max_code_retries": 3
}
```

## 🎮 使用方法

### 处理文档

```bash
# 处理文档（会覆盖原文件）
report-killer process document.docx

# 指定输出文件
report-killer process input.docx -o output.docx

# 使用自定义提示词
report-killer process input.docx --prompt "回答要简洁明了，每题不超过100字"

# 使用不同模型
report-killer process input.docx --model "openai/gpt-4"
```

### 测试功能

```bash
# 使用内置测试文档
report-killer test

# 查看配置信息
report-killer info
```

### 批量处理

```bash
# 使用 shell 循环批量处理
for file in documents/*.docx; do
    report-killer process "$file" -o "processed/$(basename $file)"
done
```

## ✨ 最新特性（v0.2.3）

### 🔄 代码执行自动重试

当代码执行失败时，系统会：
1. 显示错误信息（仅在终端）
2. 将代码和错误发送给 AI 修复
3. 重试执行修复后的代码
4. 最多重试 3 次（可配置）

**终端示例：**
```
Executing python code (attempt 1/3)...
✗ Execution failed (attempt 1/3)
Error: SyntaxError: expected ':'

Asking LLM to fix the code...
✓ Received fixed code from LLM

Executing python code (attempt 2/3)...
✓ Code execution successful
Output: Result: 42
```

### 📊 专业表格转换

AI 生成的 Markdown 表格自动转换为 Word 表格：

**AI 输出：**
```markdown
| Algorithm | Time | Space |
|-----------|------|-------|
| BFS | O(n) | O(n) |
| DFS | O(n) | O(h) |
```

**文档中显示：**
```
┌───────────┬────────┬─────────┐
│ Algorithm │ Time   │ Space   │  ← 粗体标题
├───────────┼────────┼─────────┤
│ BFS       │ O(n)   │ O(n)    │
│ DFS       │ O(n)   │ O(h)    │
└───────────┴────────┴─────────┘
```

### 🧹 清洁输出

- ✅ 文档中只包含代码和答案
- ✅ 无语言标签（如 `[Python 代码]`）
- ✅ 无错误信息
- ✅ 所有状态信息显示在终端

## 🔧 高级配置

### 环境变量

```bash
export OPENAI_API_KEY="your-api-key"
export OPENAI_API_URL="https://openrouter.ai/api/v1"
export OPENAI_MODEL="anthropic/claude-3.5-sonnet"
export HTTP_PROXY="http://127.0.0.1:7890"
export HTTPS_PROXY="http://127.0.0.1:7890"
```

### 自定义提示词示例

**控制输出格式：**
```
不使用 Markdown 格式，不使用加粗或斜体，每个答案不超过200字。
```

**要求代码示例：**
```
对于编程问题，提供完整的可运行代码，并附上注释。
```

**学术风格：**
```
使用学术写作风格，引用相关文献，提供详细的理论分析。
```

### 模型选择

**高性能模型（准确但昂贵）：**
- `anthropic/claude-3-opus`
- `openai/gpt-4-turbo`

**平衡模型（推荐）：**
- `anthropic/claude-3.5-sonnet`
- `openai/gpt-4`

**经济模型（快速但质量较低）：**
- `anthropic/claude-3-haiku`
- `openai/gpt-3.5-turbo`

### 本地 LLM 配置

使用 LM Studio 或 Ollama：

```json
{
  "api_url": "http://localhost:1234/v1",
  "api_key": "not-needed",
  "model": "local-model-name"
}
```

## 📖 工作原理

1. **文档分析**：程序读取 Word 文档，识别问题、空白和文档结构
2. **AI 处理**：将文档内容发送给 AI，让它理解问题并生成答案
3. **内容处理**：
   - 解析 AI 响应中的答案
   - 执行代码块（支持重试和自动修复）
   - 转换 Markdown 表格为 Word 表格
4. **精确插入**：将答案插入到正确的位置（问题之后，而非文档末尾）
5. **保存结果**：保存修改后的文档

## 💰 成本估算

使用 Claude 3.5 Sonnet 处理典型实验报告（约1000字，3-5个问题）：
- 输入 tokens: ~2000
- 输出 tokens: ~3000
- 通过 OpenRouter 成本: 约 $0.02-0.05

**建议：**
- 先用小文档测试
- 充值少量金额（$1-5）
- 监控 API 使用情况

## 🚨 故障排除

### API 调用失败

**401 Unauthorized**
1. 检查 API 密钥是否正确
2. 检查 API 密钥是否已过期
3. 检查账户是否有余额

**429 Too Many Requests**
1. 请求太频繁，等待一段时间后重试
2. 检查 API 配额是否用完

### 文档格式问题

**Document has incompatible format**
1. 用 Microsoft Word 或 LibreOffice 打开文档
2. 另存为新的 .docx 文件
3. 再次尝试处理

### 网络连接问题

如果在中国大陆使用，可能需要配置代理：

```bash
# 设置代理环境变量
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890

# 或通过配置命令设置
report-killer configure
```

### 答案位置不正确

**可能原因：**
- 文档结构复杂
- 问题检测失败

**解决方案：**
1. 确保问题以 `？` 或 `?` 结尾
2. 简化文档结构
3. 使用更明确的问题格式

## 📁 项目结构

```
report-killer/
├── report_killer/          # 主要代码
│   ├── __init__.py
│   ├── cli.py             # 命令行界面
│   ├── config.py          # 配置管理
│   ├── agent.py           # AI 代理核心
│   ├── docx_handler.py    # Word 文档处理
│   ├── code_executor.py   # 代码执行引擎
│   └── chart_generator.py # 图表生成
├── tests/                 # 测试文件
│   └── test_ai_doc.docx
├── documents/             # 文档存储目录
├── pyproject.toml         # 项目配置
└── README.md
```

## 🎯 支持的功能

### 文档类型
- ✅ Word .docx 格式
- ✅ 复杂文档结构
- ✅ 表格和图片

### AI 服务
- ✅ OpenRouter
- ✅ OpenAI
- ✅ Claude API
- ✅ 本地 LLM 服务

### 代码执行
- ✅ Python
- ✅ C/C++
- ✅ Java
- ✅ JavaScript（Node.js）
- ✅ 自动重试和错误修复

### 内容类型
- ✅ 文本段落
- ✅ 代码块（多种语言）
- ✅ Markdown 表格 → Word 表格
- ✅ 数学公式
- ✅ 图表生成

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

本项目使用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 🙏 致谢

- [python-docx](https://python-docx.readthedocs.io/) - Word 文档处理
- [Anthropic](https://www.anthropic.com/) - Claude API
- [Click](https://click.palletsprojects.com/) - 命令行界面
- [Rich](https://rich.readthedocs.io/) - 美观的终端输出
- [lxml](https://lxml.de/) - XML 解析和操作