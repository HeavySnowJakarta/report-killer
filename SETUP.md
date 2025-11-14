# Report Killer 安装和配置指南

## 快速开始

### 1. 安装依赖

使用 pip：
```bash
pip install -e .
```

或使用 uv（推荐）：
```bash
uv pip install -e .
```

### 2. 获取 API 密钥

Report Killer 支持任何 OpenAI 兼容的 API。你可以使用以下服务之一：

#### OpenRouter (推荐用于测试)
1. 访问 [OpenRouter](https://openrouter.ai/)
2. 注册账号
3. 在 [Keys](https://openrouter.ai/keys) 页面创建 API 密钥
4. 充值少量余额（建议 $1-5 用于测试）

#### OpenAI
1. 访问 [OpenAI Platform](https://platform.openai.com/)
2. 注册账号并绑定支付方式
3. 创建 API 密钥

#### 其他兼容服务
- Claude API（Anthropic）
- 本地 LLM 服务（如 LM Studio、Ollama 等）

### 3. 配置

运行配置命令：
```bash
report-killer configure
```

或直接创建 `config.json`：
```json
{
  "api_url": "https://openrouter.ai/api/v1",
  "api_key": "your-api-key-here",
  "model": "anthropic/claude-3.5-sonnet",
  "http_proxy": null,
  "https_proxy": null,
  "custom_prompt": "输出内容不得包含加粗文本、标题及无序列表，可以在你认为合适的地方适度插入代码。",
  "documents_dir": "documents"
}
```

### 4. 测试

使用测试命令：
```bash
report-killer test
```

这会处理 `tests/test_ai_doc.docx` 并将结果保存到 `documents/test_ai_doc_output.docx`。

## 使用示例

### 处理单个文档

```bash
# 处理文档（会覆盖原文件）
report-killer process path/to/document.docx

# 保存到新文件
report-killer process input.docx -o output.docx

# 使用自定义提示词
report-killer process input.docx --prompt "要求答案简洁，每题不超过100字"
```

### 批量处理

```bash
# 使用 shell 循环
for file in *.docx; do
    report-killer process "$file" -o "processed_$file"
done
```

## 常见问题

### API 调用失败

如果看到 `401 Unauthorized` 错误：
1. 检查 API 密钥是否正确
2. 检查 API 密钥是否已过期
3. 检查账户是否有余额

如果看到 `429 Too Many Requests` 错误：
1. 你的请求太频繁，等待一段时间后重试
2. 检查 API 配额是否用完

### 文档格式问题

如果看到 `Document has incompatible format` 错误：
1. 用 Microsoft Word 或 LibreOffice 打开文档
2. 另存为新的 .docx 文件
3. 再次尝试处理

### 代理设置

如果在中国大陆使用，可能需要配置代理：

```bash
report-killer configure
# 在提示时输入代理地址，例如：
# HTTP Proxy: http://127.0.0.1:7890
# HTTPS Proxy: http://127.0.0.1:7890
```

或设置环境变量：
```bash
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
```

## 成本估算

使用 Claude 3.5 Sonnet 处理一份典型的实验报告（约1000字，3-5个问题）：
- 输入 tokens: ~2000
- 输出 tokens: ~3000
- 通过 OpenRouter 的成本: 约 $0.02-0.05

建议：
- 先用小文档测试
- 充值少量金额（$1-5）
- 监控 API 使用情况

## 高级配置

### 自定义提示词示例

控制输出格式：
```
不使用 Markdown 格式，不使用加粗或斜体，每个答案不超过200字。
```

要求代码示例：
```
对于编程问题，提供完整的可运行代码，并附上注释。
```

学术风格：
```
使用学术写作风格，引用相关文献，提供详细的理论分析。
```

### 不同模型的选择

#### 高性能模型（准确但昂贵）
- `anthropic/claude-3-opus`
- `openai/gpt-4-turbo`

#### 平衡模型（推荐）
- `anthropic/claude-3.5-sonnet`
- `openai/gpt-4`

#### 经济模型（快速但质量较低）
- `anthropic/claude-3-haiku`
- `openai/gpt-3.5-turbo`

### 本地模型

如果使用本地 LLM（如 LM Studio）：
```json
{
  "api_url": "http://localhost:1234/v1",
  "api_key": "not-needed",
  "model": "local-model-name"
}
```

## 技术支持

遇到问题？
1. 查看 [README.md](README.md) 的故障排除章节
2. 在 GitHub 上提交 Issue
3. 检查是否有类似的已解决问题
