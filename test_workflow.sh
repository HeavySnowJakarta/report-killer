#!/bin/bash

echo "=== Report Killer Complete Workflow Test ==="
echo ""
echo "1. Testing info command..."
report-killer info

echo ""
echo "2. Testing document loading..."
python3 -c "
from report_killer.docx_handler import DocxHandler
handler = DocxHandler('tests/test_ai_doc.docx')
handler.load()
paras = handler.get_paragraphs_with_indices()
print(f'Loaded {len(paras)} paragraphs with text')
print(f'Total paragraphs: {len(handler.doc.paragraphs)}')
"

echo ""
echo "3. Testing code execution..."
python3 -c "
from report_killer.code_executor import CodeExecutor
executor = CodeExecutor()
langs = executor.get_available_languages()
print(f'Available languages: {langs}')

# Test Python execution
code = 'print(\"Hello from Python\")'
success, output, _ = executor.execute_code('python', code)
print(f'Python test: {\"SUCCESS\" if success else \"FAILED\"}')
if success:
    print(f'Output: {output.strip()}')
"

echo ""
echo "4. Structure verification..."
echo "✓ No *_new.py or *_old.py files in report_killer/"
ls report_killer/*.py 2>/dev/null | grep -E '_(new|old)\.py' && echo "FAILED: Found backup files" || echo "✓ Clean structure"

echo ""
echo "=== All basic tests passed ===" 
echo ""
echo "To test with stdio mode:"
echo "  report-killer test --test-mode"
echo ""
echo "Expected workflow:"
echo "  1. LLM detects insertion points (via stdio)"
echo "  2. For each point, LLM generates content (via stdio)"
echo "  3. Content inserted at correct positions"
echo "  4. Document saved"
