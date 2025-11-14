# Report Killer v0.2 - 使用指南

一个智能的文档填写助手，使用 AI 自动理解并填写 Word 文档中的问题和空白。

⚠️ **Version 0.2 重大更新**：
- ✅ 改用 python-docx 库（不再直接操作 XML）
- ✅ 支持代码编写和执行功能
- ✅ 添加 stdio 测试模式（无需 API 即可测试）
- ✅ 改进的插入点检测算法
- ✅ 完成度跟踪和验证

## 新功能

### 1. Stdio 测试模式

无需 API 密钥即可测试系统，你可以手动扮演 LLM：

```bash
report-killer test --test-mode
```

系统会显示提示词，你输入回答，以 `===END===` 结束输入。

### 2. 代码执行能力

系统会自动检测可用的编程环境：
- ✅ C/C++（需要 gcc/g++）
- ✅ Python 3
- ✅ Java（需要 JDK）
- ✅ JavaScript（需要 Node.js）
- ✅ Go

当文档要求编写和运行代码时，系统会：
1. 检测是否有相应的编译工具
2. 如果有，编译并运行代码
3. 将运行结果插入文档
4. 如果没有，明确告知用户缺少哪些工具

### 3. 工作区管理

所有生成的代码和编译产物存储在 `workspace/` 目录（已加入 .gitignore）

### 4. 完成度跟踪

处理文档时会显示：
- 发现的所有插入点
- 每个插入点的填写状态
- 完成率统计
- 未填写的插入点警告

## 快速开始

### 安装

```bash
pip install -e .
```

### 配置

```bash
# 方式 1：交互式配置
report-killer configure

# 方式 2：直接编辑 config.json
{
  "api_url": "https://openrouter.ai/api/v1",
  "api_key": "your-api-key-here",
  "model": "anthropic/claude-3.5-sonnet",
  "custom_prompt": "输出内容不得包含加粗文本、标题及无序列表，可以在你认为合适的地方适度插入代码。",
  "documents_dir": "documents"
}
```

### 使用

#### 测试模式（无需 API）

```bash
report-killer test --test-mode
```

你会看到类似这样的输出：
```
======================================================================
STDIO TEST MODE - Simulating LLM
======================================================================
┌─ Prompt to LLM ────────────────────────────────┐
│ 你是一个专业的学术报告撰写助手。              │
│                                                │
│ 当前需要填写的内容：                           │
│ (1)                                            │
│ ...                                            │
└────────────────────────────────────────────────┘

Enter response (end with '===END==='):
```

然后你输入 LLM 应该返回的内容，以 `===END===` 结束。

#### 生产模式（使用 API）

```bash
# 处理文档
report-killer process document.docx

# 使用测试文档
report-killer test
```

### 查看环境信息

```bash
report-killer info
```

输出示例：
```
Configuration:
  API URL: https://openrouter.ai/api/v1
  API Key: ********************
  Model: anthropic/claude-3.5-sonnet

Environment Check:
  ✓ Python 3.10+
  ✓ API Key

Code Execution:
  ✓ C
  ✓ C++
  ✓ Python
  ✓ Java
```

## 工作原理

### 插入点检测

系统会检测三种类型的插入点：

1. **问题** - 以 `？` 或 `?` 结尾的段落
2. **编号要求** - `(1)`、`(2)` 等单独成行的编号
3. **章节标题** - 包含"需要"、"要求"、"包含"等关键词的段落

### 处理流程

```
1. 加载文档
2. 分析结构，识别所有插入点
3. 对每个插入点：
   a. 构建上下文相关的提示词
   b. 调用 LLM（API 或 stdio）
   c. 解析响应
   d. 如果需要代码，提取并执行
   e. 将答案插入正确位置
4. 检查完成度
5. 保存文档
```

### 代码执行流程

当检测到需要代码时：

```
1. 从 LLM 响应中提取代码块（```language ... ```）
2. 检测是否有对应的编译/解释工具
3. 将代码写入 workspace/ 目录
4. 编译（如果需要）
5. 运行程序
6. 捕获输出
7. 将输出插入文档
```

## 示例

### 示例 1：简单问题

文档内容：
```
你所采用的估价函数f(n) = g(n) + h(n)中，g(n)和h(n)的主要作用是什么？
```

LLM 生成：
```
g(n)表示从起始节点到当前节点的实际代价，确保算法考虑已经走过的路径成本。
h(n)表示从当前节点到目标节点的估计代价，这是启发式函数，引导搜索方向。
两者结合可以在保证最优性的同时提高搜索效率。
```

### 示例 2：代码要求

文档内容：
```
编写程序实现广度优先搜索算法求解八数码问题。
```

LLM 生成（包含代码）：
````
以下是广度优先搜索实现：

```python
from collections import deque

def bfs_solve(initial_state, goal_state):
    queue = deque([initial_state])
    visited = {initial_state}
    
    while queue:
        state = queue.popleft()
        if state == goal_state:
            return True
        
        for next_state in get_neighbors(state):
            if next_state not in visited:
                visited.add(next_state)
                queue.append(next_state)
    
    return False
```
````

系统会：
1. 提取 Python 代码
2. 保存到 `workspace/code.py`
3. 运行代码（如果有测试输入）
4. 将代码和运行结果都插入文档

## 故障排除

### 问题：No code execution tools available

**原因**：系统没有检测到编译器或解释器

**解决方案**：
- C/C++: 安装 gcc/g++ 或 Visual Studio
- Python: 安装 Python 3.10+
- Java: 安装 JDK

### 问题：某些插入点未填写

查看处理结束时的警告信息：
```
⚠ Warning: 2 insertion points not filled
  ○ Para 22: (1)...
  ○ Para 50: (5) 指出无信息搜索策略...
```

这些是系统认为需要填写但未成功生成内容的位置。可能需要：
1. 改进提示词
2. 手动填写这些位置
3. 在测试模式下提供更详细的回答

### 问题：文档加载失败

**原因**：文档格式不兼容

**解决方案**：
1. 用 Microsoft Word 打开文档
2. 另存为标准 .docx 格式
3. 重新处理

## 配置选项

### custom_prompt 示例

```json
{
  "custom_prompt": "输出内容不得包含加粗文本、标题及无序列表，可以在你认为合适的地方适度插入代码。"
}
```

这会告诉 AI：
- 不使用 Markdown 格式（`**bold**`、`# header`）
- 不使用列表符号（`-`、`*`）
- 可以在适当的地方插入代码

### 代理配置

如果在中国大陆使用：
```json
{
  "http_proxy": "http://127.0.0.1:7890",
  "https_proxy": "http://127.0.0.1:7890"
}
```

## 开发和测试

### 运行 stdio 测试

```bash
# 测试单个文档
report-killer process doc.docx --test-mode

# 使用测试文档
report-killer test --test-mode
```

### 调试模式

设置自定义提示词来控制输出：
```bash
report-killer process doc.docx --prompt "请简短回答，每个问题不超过50字"
```

### 检查环境

```bash
report-killer info
```

## 与 v0.1 的区别

| 特性 | v0.1 | v0.2 |
|------|------|------|
| 文档处理 | 直接 XML 操作 | python-docx 库 |
| 测试模式 | 无 | stdio 交互模式 |
| 代码执行 | 无 | 支持多种语言 |
| 完成度跟踪 | 无 | 详细统计 |
| 插入点检测 | 基础 | 改进的多类型检测 |
| 工作区 | 无 | workspace/ 目录 |

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件。
