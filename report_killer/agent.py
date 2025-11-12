"""AI agent for processing documents."""

import os
import requests
from typing import Optional
from .config import Config
from .docx_handler import DocxHandler
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


class ReportAgent:
    """AI agent that processes Word documents."""
    
    def __init__(self, config: Config):
        """Initialize the agent with configuration."""
        self.config = config
        
        # Set up proxies if configured
        self.proxies = config.get_proxies()
        self.headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        }
        
        # For OpenRouter
        if "openrouter" in config.api_url.lower():
            self.headers["HTTP-Referer"] = "https://github.com/HeavySnowJakarta/report-killer"
            self.headers["X-Title"] = "Report Killer"
    
    def check_environment(self) -> dict:
        """Check if the required environment is available."""
        checks = {
            "python": False,
            "api_key": False,
        }
        
        # Check Python
        import sys
        if sys.version_info >= (3, 10):
            checks["python"] = True
        
        # Check API key
        if self.config.api_key:
            checks["api_key"] = True
        
        return checks
        
        # Check Python
        import sys
        if sys.version_info >= (3, 10):
            checks["python"] = True
        
        # Check API key
        if self.config.api_key:
            checks["api_key"] = True
        
        return checks
    
    def process_document(self, input_path: str, output_path: Optional[str] = None) -> bool:
        """Process a Word document and fill in answers."""
        # Validate environment
        env_checks = self.check_environment()
        if not all(env_checks.values()):
            console.print("[red]Environment check failed:[/red]")
            for check, passed in env_checks.items():
                status = "✓" if passed else "✗"
                color = "green" if passed else "red"
                console.print(f"  [{color}]{status}[/{color}] {check}")
            return False
        
        console.print(f"[cyan]Loading document:[/cyan] {input_path}")
        
        # Load document
        handler = DocxHandler(input_path)
        try:
            handler.load()
        except ValueError as e:
            console.print(f"[red]Error loading document:[/red] {e}")
            return False
        
        # Extract content
        content = handler.get_text_content()
        console.print(f"[green]Document loaded successfully[/green] ({len(content)} characters)")
        
        # Analyze structure
        structure = handler.analyze_structure()
        console.print(f"[cyan]Found {len(structure['questions'])} questions and {len(structure['blanks'])} blanks[/cyan]")
        
        # Generate content with AI
        console.print("[cyan]Generating content with AI...[/cyan]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Thinking...", total=None)
            
            generated_content = self._generate_content(content, structure)
            
            progress.update(task, completed=True)
        
        if not generated_content:
            console.print("[red]Failed to generate content[/red]")
            return False
        
        console.print("[green]Content generated successfully[/green]")
        
        # Apply changes to document
        console.print("[cyan]Applying changes to document...[/cyan]")
        self._apply_changes(handler, generated_content)
        
        # Save document
        save_path = output_path or input_path
        handler.save(save_path)
        console.print(f"[green]Document saved to:[/green] {save_path}")
        
        return True
    
    def _generate_content(self, document_content: str, structure: dict) -> dict:
        """Generate content using AI."""
        # Build prompt
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(document_content, structure)
        
        try:
            # Call AI API using OpenAI-compatible format
            api_url = self.config.api_url
            if not api_url.endswith('/chat/completions'):
                api_url = api_url.rstrip('/') + '/chat/completions'
            
            payload = {
                "model": self.config.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": 8000,
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
            
            # Extract response text
            response_text = result['choices'][0]['message']['content']
            
            # Parse the structured response
            return self._parse_ai_response(response_text, structure)
            
        except Exception as e:
            console.print(f"[red]Error calling AI API:[/red] {e}")
            if hasattr(e, 'response') and e.response:
                console.print(f"[red]Response:[/red] {e.response.text}")
            return None
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for the AI."""
        base_prompt = """你是一个专业的学术报告撰写助手。你的任务是帮助用户完成实验报告、作业等文档的填写。

你需要：
1. 仔细阅读文档内容，理解所有的问题和要求
2. 为每个问题提供准确、详细、专业的答案
3. 答案应该符合学术规范，内容充实，具有实际价值
4. 答案应该基于真实的技术知识和最佳实践
5. 对于编程作业，提供可运行的代码示例
6. 对于算法问题，提供清晰的解释和步骤
7. 不要在答案中添加无关的格式化标记

重要规则：
- 不要输出 Markdown 格式的标题（#、##等）
- 不要输出加粗文本（**text**）或斜体（*text*）
- 可以使用换行来组织内容，但不要使用无序列表符号（-、*、•）
- 如果需要代码，直接输出代码块，不需要```标记
- 答案应该直接可以插入到Word文档中"""
        
        if self.config.custom_prompt:
            base_prompt += f"\n\n用户额外要求：\n{self.config.custom_prompt}"
        
        return base_prompt
    
    def _build_user_prompt(self, document_content: str, structure: dict) -> str:
        """Build the user prompt with document content."""
        # Extract the questions
        questions = []
        for i, q in enumerate(structure.get('questions', [])):
            questions.append(f"{i+1}. {q['text']}")
        
        prompt = f"""请分析以下实验报告文档，并为其中的问题提供详细、专业的答案。

=== 文档全文 ===
{document_content}

=== 需要回答的问题 ===
{chr(10).join(questions) if questions else "没有明确的问题，请根据文档内容填写所有需要填写的部分"}

请按以下格式回答（使用<ANSWER>标签分隔每个答案）：

<ANSWER index="0">
你对第一个问题的详细回答...
</ANSWER>

<ANSWER index="1">
你对第二个问题的详细回答...
</ANSWER>

重要提示：
1. 每个答案都应该详细、专业、有深度
2. 对于算法问题，提供实现思路和关键代码
3. 对于分析问题，提供具体的数据和对比
4. 答案要符合学术规范
5. 不要使用Markdown格式标记
6. 可以适度插入代码示例来说明问题"""
        
        return prompt
    
    def _parse_ai_response(self, response_text: str, structure: dict) -> dict:
        """Parse the AI response into structured data."""
        import re
        
        # Extract answers using <ANSWER> tags
        answer_pattern = r'<ANSWER\s+index="(\d+)">(.*?)</ANSWER>'
        matches = re.findall(answer_pattern, response_text, re.DOTALL | re.IGNORECASE)
        
        answers = []
        questions = structure.get('questions', [])
        
        for index_str, answer_text in matches:
            index = int(index_str)
            if index < len(questions):
                answers.append({
                    "paragraph_index": questions[index]['index'],
                    "question": questions[index]['text'],
                    "answer": answer_text.strip(),
                    "insert_type": "after"
                })
        
        return {
            "answers": answers,
            "raw_response": response_text
        }
    
    def _apply_changes(self, handler: DocxHandler, generated_content: dict):
        """Apply the generated changes to the document."""
        if "answers" not in generated_content:
            # Fallback: just append the raw response at the end
            if "raw_response" in generated_content:
                handler.doc.add_paragraph(generated_content["raw_response"])
            return
        
        # Sort answers by paragraph index in reverse order
        # This ensures we don't mess up indices when inserting
        answers = sorted(
            generated_content["answers"],
            key=lambda x: x.get("paragraph_index", 999999),
            reverse=True
        )
        
        for answer in answers:
            para_index = answer.get("paragraph_index", -1)
            answer_text = answer.get("answer", "")
            insert_type = answer.get("insert_type", "after")
            
            if para_index < 0 or not answer_text:
                continue
            
            if insert_type == "after":
                # Insert a new paragraph after the question
                handler.insert_text_after_paragraph(para_index, answer_text)
            elif insert_type == "replace":
                # Replace blank spaces with the answer
                question = answer.get("question", "")
                if question:
                    handler.replace_text_in_paragraph(para_index, question, answer_text)
