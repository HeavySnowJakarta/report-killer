# Version 0.2.3 - Quick Reference

## What's New

### 1. Code Execution Retry (Auto-Fix)

**Before v0.2.3:**
```
Executing python code...
✗ Execution failed
Error: NameError: name 'x' is not defined
[Error inserted into document]
```

**After v0.2.3:**
```
Executing python code (attempt 1/3)...
✗ Execution failed (attempt 1/3)
Error: NameError: name 'x' is not defined

Asking LLM to fix the code...
✓ Received fixed code from LLM

Executing python code (attempt 2/3)...
✓ Code execution successful
Output:
Result: 42

[Only code inserted into document, no errors]
```

**Configuration:**
```json
{
  "max_code_retries": 3
}
```

### 2. Markdown Table → Word Table

**LLM Output:**
```markdown
| Algorithm | Time | Space |
|-----------|------|-------|
| BFS | O(n) | O(n) |
| DFS | O(n) | O(h) |
```

**Before v0.2.3:** Plain text (ugly)
```
| Algorithm | Time | Space |
|-----------|------|-------|
| BFS | O(n) | O(n) |
| DFS | O(n) | O(h) |
```

**After v0.2.3:** Proper Word table
```
┌───────────┬────────┬─────────┐
│ Algorithm │ Time   │ Space   │  (bold header)
├───────────┼────────┼─────────┤
│ BFS       │ O(n)   │ O(n)    │
│ DFS       │ O(n)   │ O(h)    │
└───────────┴────────┴─────────┘
```

### 3. Code Block Formatting

**Before v0.2.3:**
```
[Python 代码]                    ← Language label
print('Hello, World!')
```

**After v0.2.3:**
```
print('Hello, World!')           ← Clean, no label
```

### 4. Error Output Location

**Before v0.2.3:**
- Errors inserted into Word document
- Document cluttered with error messages
- Hard to distinguish between content and errors

**After v0.2.3:**
- All output (success/failure) in terminal only
- Document contains only code
- Terminal color-coded for easy reading:
  - Green: ✓ Success
  - Red: ✗ Failure
  - Yellow: ⚠ Warning
  - Cyan: ℹ Info

## Usage

### Basic Processing
```bash
$ report-killer process document.docx
```

### With Custom Retry Limit
Edit `config.json`:
```json
{
  "api_url": "https://openrouter.ai/api/v1",
  "api_key": "sk-...",
  "model": "anthropic/claude-3.5-sonnet",
  "max_code_retries": 5
}
```

### Terminal Output Example
```
Loading document: lab_report.docx
✓ Document loaded successfully

Code execution capabilities:
  ✓ C
  ✓ C++
  ✓ Python
  ✓ Java

Detecting insertion points with LLM...
Found 3 insertion points:
  ○ Para 22: 实现BFS算法
  ○ Para 34: 性能对比分析
  ○ Para 42: 实验结论

Processing insertion points...

1/3. Processing: 实现BFS算法...
  Executing python code (attempt 1/3)...
  ✗ Execution failed (attempt 1/3)
  Error:
    File "code.py", line 5
      def bfs(graph)
                   ^
    SyntaxError: expected ':'
  
  Asking LLM to fix the code...
  ✓ Received fixed code from LLM
  
  Executing python code (attempt 2/3)...
  ✓ Code execution successful
  Output:
    BFS traversal: [1, 2, 3, 4, 5]
  
  ✓ Inserted 15 paragraphs

2/3. Processing: 性能对比分析...
  ✓ Inserted 3 paragraphs (text + table)

3/3. Processing: 实验结论...
  ✓ Inserted 2 paragraphs

Completion status:
  Total points: 3
  Filled: 3
  Remaining: 0
  Rate: 100.0%

✓ Document saved to: lab_report.docx
```

## Testing

Run the test suite:
```bash
$ python test_v0.2.3.py

Testing v0.2.3 Improvements
============================================================

Test 1: Markdown Table Parsing
  ✓ Table parsing works

Test 2: Config Max Retries
  ✓ Config has max_code_retries

Test 3: Code Block Without Language Label
  ✓ No language label inserted

Test 4: Table Insertion in Document
  ✓ Table inserted successfully

Test 5: Response Parsing with Markdown Table
  ✓ Markdown table parsed from response

============================================================
Results: 5/5 tests passed
✓ All tests passed!
```

## Document Output Quality

**Clean and Professional:**
- ✓ No Markdown syntax (`**bold**`, `# headers`, etc.)
- ✓ No language labels (`[Python 代码]`)
- ✓ No error messages in document
- ✓ Proper Word tables (not plain text)
- ✓ Code with line breaks preserved
- ✓ Monospace font for code (Consolas)

**Terminal Output:**
- ✓ Color-coded for readability
- ✓ Shows execution progress
- ✓ Displays errors clearly
- ✓ Reports retry attempts
- ✓ Confirms successful fixes

## Migration from v0.2.2

No breaking changes. Optionally add to `config.json`:
```json
{
  "max_code_retries": 3
}
```

All existing functionality preserved.
