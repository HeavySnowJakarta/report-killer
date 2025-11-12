# Report Killer 演示

本文档演示 Report Killer 的完整使用流程。

## 前置要求

✅ Python 3.10+
✅ 有效的 OpenAI 兼容 API 密钥
✅ 网络连接（或配置代理）

## 安装流程

```bash
# 1. 克隆仓库
git clone https://github.com/HeavySnowJakarta/report-killer.git
cd report-killer

# 2. 安装依赖
pip install -e .
# 或使用 uv
uv pip install -e .

# 3. 验证安装
report-killer --help
```

## 配置流程

### 方法 1：交互式配置

```bash
report-killer configure
```

系统会提示输入：
```
API URL: https://openrouter.ai/api/v1
API Key: sk-or-v1-xxxxxxxxxxxx
Model: anthropic/claude-3.5-sonnet
Do you want to configure a proxy? No
Additional instructions for the AI: 输出内容不得包含加粗文本、标题及无序列表
Documents directory: documents
```

### 方法 2：手动创建配置文件

创建 `config.json`：
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

### 方法 3：环境变量

```bash
export OPENAI_API_KEY="your-api-key"
export OPENAI_API_URL="https://openrouter.ai/api/v1"
export OPENAI_MODEL="anthropic/claude-3.5-sonnet"
```

## 使用示例

### 示例 1：使用测试文档

```bash
# 运行测试
report-killer test
```

输出：
```
╭────────────────────────────────────────╮
│ 🧪 Report Killer - Test Mode           │
╰────────────────────────────────────────╯

Testing with: tests/test_ai_doc.docx
Output will be saved to: documents/test_ai_doc_output.docx

Loading document: documents/test_ai_doc_output.docx
Document loaded successfully (1238 characters)
Found 1 questions and 1 blanks
Generating content with AI...
⠋ Thinking...
Content generated successfully
Applying changes to document...
Document saved to: documents/test_ai_doc_output.docx

✓ Test completed successfully!
Check the output at: documents/test_ai_doc_output.docx
```

### 示例 2：处理自己的文档

```bash
# 处理文档（覆盖原文件）
report-killer process my_report.docx

# 保存到新文件
report-killer process my_report.docx -o my_report_filled.docx

# 使用自定义提示词
report-killer process my_report.docx \
  --prompt "每个答案不超过100字，使用学术语言"
```

### 示例 3：批量处理

```bash
# 处理目录中的所有文档
for file in reports/*.docx; do
    output="reports/filled/$(basename $file)"
    report-killer process "$file" -o "$output"
    echo "处理完成: $output"
done
```

### 示例 4：查看配置

```bash
report-killer info
```

输出：
```
╭────────────────────────────────╮
│ ℹ️  Report Killer - Information │
╰────────────────────────────────╯

Configuration:
  API URL: https://openrouter.ai/api/v1
  API Key: ********************
  Model: anthropic/claude-3.5-sonnet
  HTTP Proxy: Not set
  HTTPS Proxy: Not set
  Custom Prompt: 输出内容不得包含加粗文本、标题及无序列表
  Documents Dir: documents

Environment Check:
  ✓ python
  ✓ api_key
```

## 文档处理示例

### 输入文档（测试文档节选）

```
实验二  八数码问题

实验目的
...

五、学生实验报告要求

2、思考并解答以下问题

你所采用的估价函数f(n) = g(n) + h(n)中，g(n)和h(n)的主要作用是什么？

结合本实验举例说明不同启发策略对实验的效果有何影响？
```

### 处理过程

1. **文档加载**：解析 Word 文档，提取所有文本
2. **结构分析**：识别 1 个问题和 1 个空白
3. **AI 处理**：
   - 发送文档内容和问题到 AI
   - AI 理解问题并生成答案
   - 使用 `<ANSWER>` 标签格式返回
4. **内容插入**：在每个问题后插入对应答案
5. **保存文档**：保存修改后的文档

### 输出文档（处理后）

```
实验二  八数码问题

实验目的
...

五、学生实验报告要求

2、思考并解答以下问题

你所采用的估价函数f(n) = g(n) + h(n)中，g(n)和h(n)的主要作用是什么？

【AI 生成的答案】
g(n)表示从起始节点到当前节点的实际代价，也就是已经走过的路径成本。
它确保算法考虑到达当前状态的实际花费。

h(n)表示从当前节点到目标节点的估计代价，这是一个启发式函数。
它帮助算法预测未来可能的成本，引导搜索向目标方向前进。

两者结合使用可以在搜索过程中既考虑已走过的代价，也考虑未来的预估代价，
从而在保证找到最优解的同时提高搜索效率。

结合本实验举例说明不同启发策略对实验的效果有何影响？

【AI 生成的答案】
...
```

## 技术细节

### 文档修改方式

Report Killer 使用**直接 XML 操作**而非 python-docx 库：

1. 解压 docx 文件（实际是 ZIP）
2. 解析 `word/document.xml`
3. 在 XML 中定位问题段落
4. 在问题后插入新的段落元素
5. 重新打包成 docx

这种方式的优势：
- ✅ 支持非标准 OOXML 格式
- ✅ 精确控制插入位置
- ✅ 保持原文档格式
- ✅ 不修改问题内容

### AI 提示词设计

系统提示词：
```
你是一个专业的学术报告撰写助手。
你需要为每个问题提供准确、详细、专业的答案。
答案应该符合学术规范，内容充实，具有实际价值。

重要规则：
- 不要输出 Markdown 格式的标题
- 不要输出加粗文本或斜体
- 可以使用换行来组织内容
- 如果需要代码，直接输出代码块
```

用户提示词：
```
请分析以下实验报告文档，并为其中的问题提供详细、专业的答案。

=== 文档全文 ===
[文档内容]

=== 需要回答的问题 ===
1. 你所采用的估价函数f(n) = g(n) + h(n)中，g(n)和h(n)的主要作用是什么？

请按以下格式回答：

<ANSWER index="0">
你对第一个问题的详细回答...
</ANSWER>
```

### 响应解析

使用正则表达式提取答案：
```python
pattern = r'<ANSWER\s+index="(\d+)">(.*?)</ANSWER>'
matches = re.findall(pattern, response, re.DOTALL)
```

### 插入策略

倒序插入避免索引错位：
```python
answers = sorted(answers, key=lambda x: x['index'], reverse=True)
for answer in answers:
    insert_after_paragraph(answer['index'], answer['text'])
```

## 成本示例

处理测试文档的预估成本（使用 Claude 3.5 Sonnet via OpenRouter）：

- **输入 tokens**: ~2000
- **输出 tokens**: ~3000
- **总成本**: ~$0.03

实际成本取决于：
- 文档长度
- 问题数量
- 答案详细程度
- 使用的模型

## 故障排除

### 问题 1：API 调用失败

```
Error calling AI API: 401 Unauthorized
```

**解决方案**：
1. 检查 API 密钥是否正确
2. 确认账户有余额
3. 验证 API URL 是否正确

### 问题 2：文档格式不兼容

```
Document has incompatible format
```

**解决方案**：
用 Microsoft Word 重新保存文档为 .docx 格式

### 问题 3：答案位置不对

**可能原因**：
- 文档结构复杂
- 问题检测失败

**解决方案**：
1. 确保问题以 `？` 或 `?` 结尾
2. 简化文档结构
3. 使用更明确的问题格式

## 高级用法

### 自定义模型

```bash
# 使用 GPT-4
report-killer process doc.docx --model "openai/gpt-4"

# 使用经济模型
report-killer process doc.docx --model "anthropic/claude-3-haiku"
```

### 使用代理

```bash
# 设置代理
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890

# 然后正常使用
report-killer process doc.docx
```

### 本地 LLM

使用 LM Studio 或 Ollama：

```json
{
  "api_url": "http://localhost:1234/v1",
  "api_key": "not-needed",
  "model": "llama2"
}
```

## 总结

Report Killer 是一个强大而灵活的文档自动填写工具，它：

✅ 支持复杂的 Word 文档格式
✅ 使用先进的 AI 模型生成高质量答案
✅ 精确插入答案到正确位置
✅ 完全保护原文档的问题和格式
✅ 提供灵活的配置选项
✅ 易于使用和部署

无论是处理课程作业、实验报告，还是其他需要填写的文档，Report Killer 都能显著提高效率！
