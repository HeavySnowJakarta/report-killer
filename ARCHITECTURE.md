# Report Killer 架构文档

## 概述

Report Killer 是一个基于 AI 的文档自动填写工具，能够读取 Word 文档，理解其中的问题，并使用 AI 生成答案直接插入到文档的正确位置。

## 架构设计

### 核心组件

```
report_killer/
├── __init__.py          # 包初始化
├── cli.py               # 命令行界面
├── config.py            # 配置管理
├── agent.py             # AI 代理核心逻辑
└── docx_handler.py      # Word 文档处理
```

### 1. CLI (cli.py)

命令行界面模块，提供以下命令：
- `configure`: 配置 API 密钥、模型等设置
- `process`: 处理单个文档
- `test`: 使用测试文档进行测试
- `info`: 显示当前配置和环境状态

使用 Click 库构建，Rich 库提供美观的终端输出。

### 2. Config (config.py)

配置管理模块，负责：
- 从 `config.json` 加载配置
- 从环境变量读取配置
- 保存配置到文件
- 管理代理设置

配置项：
- `api_url`: API 端点 URL
- `api_key`: API 密钥
- `model`: 使用的模型名称
- `http_proxy` / `https_proxy`: 代理设置
- `custom_prompt`: 用户自定义提示词
- `documents_dir`: 文档存储目录

### 3. DocxHandler (docx_handler.py)

Word 文档处理模块，采用直接 XML 操作方式：

#### 为什么使用 XML 而不是 python-docx？

测试文档使用了 OOXML Transitional 格式（`http://purl.oclc.org/ooxml/`），而 python-docx 只支持标准 OOXML 格式（`http://schemas.openxmlformats.org/`）。直接操作 XML 可以：
1. 支持更多文档格式
2. 更精确地控制插入位置
3. 避免格式丢失

#### 核心功能

1. **加载文档**：
   - 解压 docx 文件（实际是 ZIP 格式）
   - 使用 lxml 解析 `word/document.xml`
   - 自动检测 OOXML 命名空间

2. **分析结构**：
   - 识别所有段落
   - 检测问题（以 `？` 或 `?` 结尾的段落）
   - 检测空白填写区（包含连续空格或下划线）

3. **插入内容**：
   - 在指定段落后插入新段落
   - 替换段落中的文本
   - 保持文档原有格式

4. **保存文档**：
   - 将修改后的 XML 写回
   - 重新打包成 docx 文件

### 4. ReportAgent (agent.py)

AI 代理模块，核心处理流程：

```
加载文档 → 分析结构 → 生成提示词 → 调用 AI API → 解析响应 → 插入答案 → 保存文档
```

#### AI 交互流程

1. **构建系统提示词**：
   - 定义 AI 的角色和任务
   - 添加输出格式要求
   - 包含用户自定义提示词

2. **构建用户提示词**：
   - 提供完整文档内容
   - 列出所有检测到的问题
   - 指定回答格式（使用 `<ANSWER>` 标签）

3. **调用 AI API**：
   - 使用标准 OpenAI-compatible API 格式
   - 支持代理设置
   - 支持多种 AI 服务（OpenRouter、OpenAI 等）

4. **解析响应**：
   - 提取 `<ANSWER index="N">` 标签中的内容
   - 将答案与问题位置关联
   - 生成插入指令

5. **应用更改**：
   - 按照段落索引倒序插入（避免索引错位）
   - 使用 DocxHandler 执行实际插入操作

## 技术栈

### 核心依赖

- **lxml**: XML 解析和操作
  - 处理 Word 文档的 XML 结构
  - 支持命名空间操作
  - 提供 `getparent()` 等便利方法

- **requests**: HTTP 客户端
  - 调用 OpenAI-compatible API
  - 支持代理设置

- **click**: 命令行界面
  - 命令和参数解析
  - 自动生成帮助信息

- **rich**: 终端美化
  - 彩色输出
  - 进度指示器
  - 表格和面板

### 文件格式

#### Word 文档结构

```
document.docx (ZIP文件)
├── [Content_Types].xml
├── _rels/
│   └── .rels
├── word/
│   ├── document.xml       # 主要内容
│   ├── _rels/
│   ├── media/             # 图片等资源
│   ├── theme/
│   ├── styles.xml
│   └── ...
└── docProps/
```

#### document.xml 结构

```xml
<w:document>
  <w:body>
    <w:p>                  <!-- 段落 -->
      <w:r>                <!-- 文本运行 -->
        <w:t>文本内容</w:t>
      </w:r>
    </w:p>
    ...
  </w:body>
</w:document>
```

## 工作流程

### 用户视角

```
1. 安装并配置 Report Killer
2. 准备包含问题的 Word 文档
3. 运行 report-killer process document.docx
4. 查看生成的文档
```

### 内部流程

```
1. CLI 解析命令行参数
2. Config 加载配置
3. Agent 初始化
   ├─ 设置 API 客户端
   └─ 配置代理
4. DocxHandler 加载文档
   ├─ 解压 docx
   ├─ 解析 XML
   └─ 分析结构
5. Agent 调用 AI
   ├─ 构建提示词
   ├─ 发送 API 请求
   └─ 解析响应
6. DocxHandler 应用更改
   ├─ 插入答案
   └─ 保存文档
7. 完成并输出结果
```

## 设计考虑

### 1. 为什么不使用 python-docx？

- **兼容性问题**：python-docx 对非标准 OOXML 格式支持不佳
- **控制精度**：直接 XML 操作提供更精确的控制
- **格式保持**：避免库的默认行为可能改变文档格式

### 2. 为什么使用标签格式而不是 JSON？

```xml
<!-- 更可靠 -->
<ANSWER index="0">
答案内容
</ANSWER>

<!-- vs JSON（AI 可能格式化不当） -->
{
  "answers": [
    {"index": 0, "content": "答案内容"}
  ]
}
```

- AI 生成 JSON 容易出错（特别是包含引号时）
- 标签格式更容易用正则表达式提取
- 更宽容（即使格式稍有偏差也能解析）

### 3. 为什么倒序插入？

```python
# 正序插入会导致索引错位
for answer in answers:  # 索引 [1, 3, 5]
    insert_at(answer.index)  # 插入后索引变成 [2, 4, 6]

# 倒序插入保持索引有效
for answer in reversed(answers):  # 索引 [5, 3, 1]
    insert_at(answer.index)  # 后面的索引不受影响
```

### 4. 临时目录管理

使用 `tempfile.mkdtemp()` 创建临时目录：
- 提取 docx 内容
- 修改 XML
- 重新打包

使用 `__del__` 方法清理：
```python
def __del__(self):
    if self._temp_dir:
        shutil.rmtree(self._temp_dir)
```

## 扩展性

### 添加新的文档格式

继承 `DocxHandler` 并实现相同的接口：
- `load()`
- `get_text_content()`
- `analyze_structure()`
- `insert_text_after_paragraph()`
- `save()`

### 支持新的 AI 服务

只需修改 `agent.py` 中的 API 调用逻辑：
- 保持请求格式为 OpenAI-compatible
- 或添加新的请求格式分支

### 添加新功能

- **图片插入**: 在 DocxHandler 中添加图片元素创建
- **表格填写**: 解析和操作表格 XML 元素
- **多语言支持**: 在提示词中添加语言参数
- **批量处理**: 在 CLI 中添加批处理命令

## 安全考虑

### API 密钥管理

- 存储在本地 `config.json`
- 加入 `.gitignore`
- 支持环境变量覆盖
- 显示时进行脱敏

### 代理安全

- 支持 HTTP/HTTPS 代理
- 不记录敏感信息
- 允许用户自行配置

### 数据隐私

- 文档在本地处理
- 仅通过 API 发送文档内容到 AI 服务
- 不上传到任何第三方服务器
- 用户完全控制数据流向

## 性能优化

### 1. 懒加载

文档仅在需要时加载：
```python
if not self.paragraphs:
    self.load()
```

### 2. 一次性操作

批量插入而不是逐个操作：
```python
for answer in sorted_answers:
    insert(answer)  # 一次性插入所有答案
save()  # 只保存一次
```

### 3. 内存管理

使用临时文件而不是全部加载到内存：
- 大文档友好
- 避免内存溢出

## 故障处理

### 文档加载失败

```python
try:
    doc = Document(filepath)
except KeyError:
    # 尝试修复命名空间
    fix_namespace()
```

### API 调用失败

```python
try:
    response = requests.post(...)
    response.raise_for_status()
except requests.HTTPError as e:
    console.print(f"[red]Error: {e}[/red]")
    return None
```

### 解析失败回退

```python
# 尝试标签格式
if not parse_tags(response):
    # 回退到原始文本
    use_raw_text(response)
```

## 测试策略

### 单元测试

- `test_docx_handler.py`: 文档加载、修改、保存
- `test_agent.py`: 提示词构建、响应解析
- `test_config.py`: 配置加载和保存

### 集成测试

- 端到端文档处理流程
- API 调用模拟
- 多种文档格式测试

### 手动测试

使用 `tests/test_ai_doc.docx`:
```bash
report-killer test
```

## 未来改进

### 短期

- [ ] 添加更多文档格式支持（PDF、TXT）
- [ ] 改进问题检测算法
- [ ] 支持表格内容填写
- [ ] 添加单元测试

### 长期

- [ ] 图形用户界面
- [ ] 本地 AI 模型集成
- [ ] 批量处理优化
- [ ] 多语言界面支持
- [ ] 云端服务版本
