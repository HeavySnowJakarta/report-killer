"""AI agent for processing documents with LLM-based insertion point detection."""

import os
import sys
import requests
import json
import re
from typing import Optional, List, Dict, Tuple
from .config import Config
from .docx_handler import DocxHandler, InsertionPoint
from .code_executor import CodeExecutor
from .chart_generator import ChartGenerator
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.table import Table

console = Console()


class ReportAgent:
    """AI agent that processes Word documents with LLM-based analysis."""
    
    def __init__(self, config: Config, test_mode: bool = False):
        """Initialize the agent with configuration."""
        self.config = config
        self.test_mode = test_mode
        
        # Set up proxies if configured
        self.proxies = config.get_proxies()
        
        if not test_mode:
            self.headers = {
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json",
            }
            
            # For OpenRouter
            if "openrouter" in config.api_url.lower():
                self.headers["HTTP-Referer"] = "https://github.com/HeavySnowJakarta/report-killer"
                self.headers["X-Title"] = "Report Killer"
        
        # Initialize code executor
        self.executor = CodeExecutor()
        
        # Initialize chart generator
        self.chart_generator = ChartGenerator()
    
    def check_environment(self) -> dict:
        """Check if the required environment is available."""
        checks = {
            "python": False,
            "api_key": False,
            "code_execution": {},
        }
        
        # Check Python
        import sys
        if sys.version_info >= (3, 10):
            checks["python"] = True
        
        # Check API key (not needed in test mode)
        if self.test_mode or self.config.api_key:
            checks["api_key"] = True
        
        # Check code execution capabilities
        available_langs = self.executor.get_available_languages()
        checks["code_execution"] = {
            "available": available_langs,
            "tools": self.executor.available_tools,
        }
        
        return checks
    
    def process_document(self, input_path: str, output_path: Optional[str] = None) -> bool:
        """Process a Word document and fill in answers."""
        # Validate environment
        env_checks = self.check_environment()
        if not all([env_checks["python"], env_checks["api_key"]]):
            console.print("[red]Environment check failed:[/red]")
            for check, passed in env_checks.items():
                if check != "code_execution":
                    status = "✓" if passed else "✗"
                    color = "green" if passed else "red"
                    console.print(f"  [{color}]{status}[/{color}] {check}")
            return False
        
        # Show code execution capabilities
        console.print("\n[cyan]Code execution capabilities:[/cyan]")
        for lang in env_checks["code_execution"]["available"]:
            console.print(f"  ✓ {lang}")
        
        if not env_checks["code_execution"]["available"]:
            console.print("  [yellow]⚠ No code execution tools detected[/yellow]")
        
        console.print(f"\n[cyan]Loading document:[/cyan] {input_path}")
        
        # Load document
        handler = DocxHandler(input_path)
        try:
            handler.load()
        except Exception as e:
            console.print(f"[red]Error loading document:[/red] {e}")
            return False
        
        # Extract content
        full_content = handler.get_text_content()
        console.print(f"[green]Document loaded successfully[/green] ({len(full_content)} characters)")
        
        # Use LLM to detect insertion points
        console.print(f"\n[cyan]Detecting insertion points with LLM...[/cyan]")
        insertion_points = self._detect_insertion_points_with_llm(handler, full_content)
        
        if not insertion_points:
            console.print("[yellow]No insertion points found. Document may already be complete.[/yellow]")
            return True
        
        console.print(f"\n[cyan]Found {len(insertion_points)} insertion points:[/cyan]")
        for point in insertion_points:
            console.print(f"  {point}")
        
        # Process each insertion point
        console.print(f"\n[cyan]Processing insertion points...[/cyan]")
        
        for i, point in enumerate(insertion_points, 1):
            console.print(f"\n[bold]{i}/{len(insertion_points)}. Processing:[/bold] {point.description[:60]}...")
            
            # Generate content for this point with full context
            generated = self._generate_content_for_point(point, full_content)
            
            if generated:
                # Insert into document
                handler.insert_content_at_point(point, generated)
                console.print(f"  [green]✓ Inserted {len(generated)} paragraphs[/green]")
            else:
                console.print(f"  [red]✗ Failed to generate content[/red]")
        
        # Check completion status
        status = handler.get_completion_status()
        console.print(f"\n[cyan]Completion status:[/cyan]")
        console.print(f"  Total points: {status['total']}")
        console.print(f"  Filled: {status['filled']}")
        console.print(f"  Remaining: {status['remaining']}")
        console.print(f"  Rate: {status['completion_rate']:.1%}")
        
        if status['remaining'] > 0:
            console.print(f"\n[yellow]⚠ Warning: {status['remaining']} insertion points not filled[/yellow]")
            for point in status['points']:
                if not point.filled:
                    console.print(f"  ○ {point.description[:60]}...")
        
        # Save document
        save_path = output_path or input_path
        handler.save(save_path)
        console.print(f"\n[green]✓ Document saved to:[/green] {save_path}")
        
        return status['remaining'] == 0
    
    def _detect_insertion_points_with_llm(self, handler: DocxHandler, full_content: str) -> List[InsertionPoint]:
        """Use LLM to detect insertion points in the document."""
        paragraphs = handler.get_paragraphs_with_indices()
        
        # Build prompt for LLM to analyze insertion points
        prompt = f"""请分析以下Word文档，找出所有需要填写内容的位置。

文档内容：
{full_content}

所有段落（带索引）：
"""
        for idx, text in paragraphs:
            prompt += f"{idx}: {text}\n"
        
        prompt += """
请列出所有需要填写内容的位置，对于每个位置，提供：
1. 段落索引（para_index）
2. 描述（description）- 说明这个位置需要填写什么

以JSON格式返回，格式如下：
{
  "insertion_points": [
    {
      "para_index": 22,
      "description": "需要实现八数码问题的BFS、DFS和A*算法"
    }
  ]
}

注意：
- 只标注真正需要填写的位置（如实验内容、代码实现要求、未回答的问题等）
- 已经有答案的问题不要标注
- 忽略标题、说明性段落
"""
        
        # Get LLM response
        if self.test_mode:
            response = self._stdio_interaction(prompt)
        else:
            response = self._api_interaction(prompt)
        
        # Parse response
        points = self._parse_insertion_points_response(response, handler)
        handler.set_insertion_points(points)
        
        return points
    
    def _parse_insertion_points_response(self, response: str, handler: DocxHandler) -> List[InsertionPoint]:
        """Parse LLM response to extract insertion points."""
        points = []
        
        try:
            # Try to extract JSON
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                
                if "insertion_points" in data:
                    for item in data["insertion_points"]:
                        para_index = item.get("para_index")
                        description = item.get("description", "")
                        
                        if para_index is not None:
                            # Get context around this point
                            before, after = handler.get_context_around_index(para_index)
                            point = InsertionPoint(para_index, description, before, after)
                            points.append(point)
        except Exception as e:
            console.print(f"[yellow]Warning: Failed to parse insertion points: {e}[/yellow]")
        
        return points
    
    def _generate_content_for_point(self, point: InsertionPoint, full_content: str) -> List[dict]:
        """Generate content for a specific insertion point with full context."""
        # Build context-aware prompt
        prompt = self._build_prompt_for_point(point, full_content)
        
        # Get AI response
        if self.test_mode:
            response = self._stdio_interaction(prompt)
        else:
            response = self._api_interaction(prompt)
        
        if not response:
            return []
        
        # Parse response into structured content
        content_items = self._parse_response_to_structured_content(response, point)
        
        return content_items
    
    def _parse_response_to_structured_content(self, response: str, point: InsertionPoint) -> List[dict]:
        """Parse AI response into structured content (text, code, tables, images)."""
        content = []
        
        # Remove code blocks and process them separately
        code_blocks = []
        code_pattern = r'```(\w+)?\n(.*?)```'
        
        def replace_code_block(match):
            language = match.group(1) or 'python'
            code = match.group(2)
            code_blocks.append((language.lower(), code))
            return f"<<<CODE_BLOCK_{len(code_blocks)-1}>>>"
        
        # Replace code blocks with placeholders
        text_content = re.sub(code_pattern, replace_code_block, response, flags=re.DOTALL)
        
        # Parse text into paragraphs
        lines = text_content.strip().split('\n')
        current_para = []
        
        for line in lines:
            line = line.strip()
            
            # Check for code block placeholder
            code_match = re.match(r'<<<CODE_BLOCK_(\d+)>>>', line)
            if code_match:
                # Save current paragraph
                if current_para:
                    para_text = ' '.join(current_para)
                    # Remove markdown formatting
                    para_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', para_text)
                    para_text = re.sub(r'\*([^*]+)\*', r'\1', para_text)
                    content.append({'type': 'text', 'data': para_text})
                    current_para = []
                
                # Process code block
                code_idx = int(code_match.group(1))
                if code_idx < len(code_blocks):
                    language, code = code_blocks[code_idx]
                    
                    # Check if it's a chart generation code
                    if language == 'python' and ('plt.' in code or 'matplotlib' in code):
                        # Generate chart
                        chart_path = self.chart_generator.parse_chart_from_code(code)
                        if chart_path:
                            console.print(f"[green]✓ Generated chart: {chart_path}[/green]")
                            content.append({'type': 'image', 'data': chart_path, 'width': 5.0})
                            content.append({'type': 'code', 'data': code, 'language': language})
                        else:
                            console.print(f"[yellow]⚠ Failed to generate chart[/yellow]")
                            content.append({'type': 'code', 'data': code, 'language': language})
                    else:
                        # Regular code block
                        content.append({'type': 'code', 'data': code, 'language': language})
                        
                        # Execute if applicable
                        can_execute, message = self.executor.can_execute_language(language)
                        if can_execute and ("代码" in point.description or "程序" in point.description or "实现" in point.description):
                            console.print(f"\n[cyan]Executing {language} code...[/cyan]")
                            success, output, code_file = self.executor.execute_code(language, code)
                            
                            if success:
                                console.print(f"[green]✓ Execution successful[/green]")
                                content.append({'type': 'text', 'data': f"程序执行结果：\n{output}"})
                            else:
                                console.print(f"[red]✗ Execution failed[/red]")
                                content.append({'type': 'text', 'data': f"程序执行失败：\n{output}"})
                continue
            
            # Skip empty lines or markdown headers
            if not line or line.startswith('#'):
                if current_para:
                    para_text = ' '.join(current_para)
                    para_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', para_text)
                    para_text = re.sub(r'\*([^*]+)\*', r'\1', para_text)
                    content.append({'type': 'text', 'data': para_text})
                    current_para = []
                continue
            
            # Remove markdown formatting
            line = re.sub(r'\*\*([^*]+)\*\*', r'\1', line)
            line = re.sub(r'\*([^*]+)\*', r'\1', line)
            
            current_para.append(line)
        
        # Add last paragraph
        if current_para:
            para_text = ' '.join(current_para)
            content.append({'type': 'text', 'data': para_text})
        
        return content
    
    def _build_prompt_for_point(self, point: InsertionPoint, full_content: str) -> str:
        """Build a focused prompt with full context for a specific insertion point."""
        base_prompt = f"""你是一个专业的学术报告撰写助手。

=== 完整文档内容 ===
{full_content}

=== 当前需要填写的位置 ===
段落索引：{point.para_index}
需求描述：{point.description}

=== 上下文 ===
前文：
{point.context_before}

当前位置需要填写的内容

后文：
{point.context_after}

请为这个位置提供详细、专业的内容。要求：
1. 内容要详实、有深度，符合学术规范
2. 如果需要代码，请提供完整可运行的代码（使用```language标记）
3. 如果需要实验结果，请说明实验设计和预期结果
4. 如果需要分析对比，请提供具体数据和图表说明
5. 不要使用Markdown格式的加粗（**）、标题（#）、列表符号（-、*）
"""
        
        if self.config.custom_prompt:
            base_prompt += f"\n\n用户额外要求：\n{self.config.custom_prompt}"
        
        # Add code execution context
        available_langs = self.executor.get_available_languages()
        if available_langs:
            base_prompt += f"\n\n可用的编程语言：{', '.join(available_langs)}"
            base_prompt += "\n如果需要代码，请优先使用可用的语言。"
        
        return base_prompt
    
    def _stdio_interaction(self, prompt: str) -> str:
        """Interact with LLM via stdio (for testing)."""
        console.print("\n" + "="*70, style="cyan")
        console.print("[bold cyan]STDIO TEST MODE - Simulating LLM[/bold cyan]")
        console.print("="*70, style="cyan")
        
        console.print(Panel(prompt, title="Prompt to LLM", border_style="blue", expand=False))
        
        console.print("\n[yellow]Enter response (end with '===END==='):[/yellow]")
        
        lines = []
        while True:
            try:
                line = input()
                if line.strip() == "===END===":
                    break
                lines.append(line)
            except EOFError:
                break
        
        response = "\n".join(lines)
        
        console.print("\n[green]Response received[/green]")
        
        return response
    
    def _api_interaction(self, prompt: str) -> str:
        """Interact with LLM via API."""
        try:
            api_url = self.config.api_url
            if not api_url.endswith('/chat/completions'):
                api_url = api_url.rstrip('/') + '/chat/completions'
            
            payload = {
                "model": self.config.model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 8000,
                "temperature": 0.7,
            }
            
            response = requests.post(
                api_url,
                headers=self.headers,
                json=payload,
                proxies=self.proxies,
                timeout=180,
            )
            
            response.raise_for_status()
            result = response.json()
            
            return result['choices'][0]['message']['content']
            
        except Exception as e:
            console.print(f"[red]Error calling AI API:[/red] {e}")
            return ""
    
    def _parse_response(self, response: str) -> List[str]:
        """Parse AI response into paragraphs."""
        paragraphs = []
        
        # First, try to clean up the response
        lines = response.strip().split('\n')
        
        current_para = []
        for line in lines:
            line = line.strip()
            
            # Skip empty lines or markdown headers
            if not line or line.startswith('#'):
                if current_para:
                    paragraphs.append(' '.join(current_para))
                    current_para = []
                continue
            
            # Remove markdown bold/italic
            line = re.sub(r'\*\*([^*]+)\*\*', r'\1', line)
            line = re.sub(r'\*([^*]+)\*', r'\1', line)
            
            current_para.append(line)
        
        if current_para:
            paragraphs.append(' '.join(current_para))
        
        return paragraphs
    
    def _extract_and_execute_code(self, response: str) -> List[str]:
        """Extract code from response and execute it."""
        results = []
        
        # Try to find code blocks (```language...```)
        code_pattern = r'```(\w+)?\n(.*?)```'
        matches = re.findall(code_pattern, response, re.DOTALL)
        
        for language, code in matches:
            if not language:
                language = 'python'  # Default
            
            language = language.lower()
            
            # Check if we can execute this language
            can_execute, message = self.executor.can_execute_language(language)
            
            if can_execute:
                console.print(f"\n[cyan]Executing {language} code...[/cyan]")
                success, output, code_file = self.executor.execute_code(language, code)
                
                if success:
                    console.print(f"[green]✓ Execution successful[/green]")
                    results.append(f"程序执行结果：\n{output}")
                else:
                    console.print(f"[red]✗ Execution failed[/red]")
                    results.append(f"程序执行失败：\n{output}")
            else:
                console.print(f"[yellow]⚠ Cannot execute {language}: {message}[/yellow]")
                results.append(f"注意：需要{language}环境。{message}")
        
        return results
