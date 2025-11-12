"""AI agent for processing documents with stdio test mode support."""

import os
import sys
import requests
import json
import re
from typing import Optional, List, Dict, Tuple
from .config import Config
from .docx_handler import DocxHandler, InsertionPoint
from .code_executor import CodeExecutor
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.table import Table

console = Console()


class ReportAgent:
    """AI agent that processes Word documents with code execution capability."""
    
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
        content = handler.get_text_content()
        console.print(f"[green]Document loaded successfully[/green] ({len(content)} characters)")
        
        # Analyze structure
        structure = handler.analyze_structure()
        insertion_points = handler.find_all_insertion_points()
        
        console.print(f"\n[cyan]Found {len(insertion_points)} insertion points:[/cyan]")
        for point in insertion_points:
            console.print(f"  {point}")
        
        if not insertion_points:
            console.print("[yellow]No insertion points found. Document may already be complete.[/yellow]")
            return True
        
        # Process each insertion point
        console.print(f"\n[cyan]Processing insertion points...[/cyan]")
        
        for point in insertion_points:
            console.print(f"\n[bold]Processing:[/bold] {point.description[:60]}...")
            
            # Generate content for this point
            generated = self._generate_content_for_point(point, content, structure)
            
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
        
        return True
    
    def _generate_content_for_point(self, point: InsertionPoint, 
                                    full_content: str, structure: dict) -> List[str]:
        """Generate content for a specific insertion point."""
        # Build context-aware prompt
        prompt = self._build_prompt_for_point(point, full_content, structure)
        
        # Get AI response
        if self.test_mode:
            response = self._stdio_interaction(prompt)
        else:
            response = self._api_interaction(prompt)
        
        if not response:
            return []
        
        # Parse response into paragraphs
        paragraphs = self._parse_response(response, point)
        
        # Check if code execution is needed
        if "代码" in point.description or "程序" in point.description or "实现" in point.description:
            # Try to extract and execute code
            code_results = self._extract_and_execute_code(response)
            if code_results:
                paragraphs.extend(code_results)
        
        return paragraphs
    
    def _build_prompt_for_point(self, point: InsertionPoint, 
                                full_content: str, structure: dict) -> str:
        """Build a focused prompt for a specific insertion point."""
        base_prompt = f"""你是一个专业的学术报告撰写助手。

当前需要填写的内容：
{point.description}

文档上下文：
{full_content[:2000]}

请提供详细、专业的答案。注意：
1. 如果需要代码，请提供完整可运行的代码
2. 如果需要实验结果，请说明如何获得
3. 答案要符合学术规范
4. 不要使用Markdown格式标记（如**、#等）
"""
        
        if self.config.custom_prompt:
            base_prompt += f"\n\n用户额外要求：\n{self.config.custom_prompt}"
        
        # Add code execution context
        available_langs = self.executor.get_available_languages()
        if available_langs:
            base_prompt += f"\n\n可用的编程语言：{', '.join(available_langs)}"
        
        return base_prompt
    
    def _stdio_interaction(self, prompt: str) -> str:
        """Interact with LLM via stdio (for testing)."""
        console.print("\n" + "="*70, style="cyan")
        console.print("[bold cyan]STDIO TEST MODE - Simulating LLM[/bold cyan]")
        console.print("="*70, style="cyan")
        
        console.print(Panel(prompt, title="Prompt to LLM", border_style="blue"))
        
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
        
        console.print("\n[green]Response received:[/green]")
        console.print(Panel(response[:200] + "..." if len(response) > 200 else response, 
                          border_style="green"))
        
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
                "max_tokens": 4000,
                "temperature": 0.7,
            }
            
            response = requests.post(
                api_url,
                headers=self.headers,
                json=payload,
                proxies=self.proxies,
                timeout=120,
            )
            
            response.raise_for_status()
            result = response.json()
            
            return result['choices'][0]['message']['content']
            
        except Exception as e:
            console.print(f"[red]Error calling AI API:[/red] {e}")
            return ""
    
    def _parse_response(self, response: str, point: InsertionPoint) -> List[str]:
        """Parse AI response into paragraphs."""
        # Split by double newlines
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
                    results.append(f"代码执行结果：\n{output}")
                else:
                    console.print(f"[red]✗ Execution failed[/red]")
                    results.append(f"代码执行失败：\n{output}")
            else:
                console.print(f"[yellow]⚠ Cannot execute {language}: {message}[/yellow]")
                results.append(f"注意：需要{language}环境，但当前系统不可用。{message}")
        
        return results
