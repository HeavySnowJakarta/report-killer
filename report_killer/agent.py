"""AI agent for processing documents."""

import os
from typing import Optional
from anthropic import Anthropic
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
        if config.get_proxies():
            for key, value in config.get_proxies().items():
                if value:
                    os.environ[key.upper() + "_PROXY"] = value
        
        # Initialize Anthropic client
        # For OpenRouter or other OpenAI-compatible APIs
        self.client = Anthropic(
            api_key=config.api_key,
            base_url=config.api_url if "anthropic" not in config.api_url.lower() else None,
        )
        self.model = config.model
    
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
            # Call AI API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=8000,
                temperature=0.7,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            # Parse response
            response_text = response.content[0].text
            
            # Parse the structured response
            return self._parse_ai_response(response_text, structure)
            
        except Exception as e:
            console.print(f"[red]Error calling AI API:[/red] {e}")
            return None
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for the AI."""
        base_prompt = """你是一个专业的学术报告撰写助手。你的任务是帮助用户完成实验报告、作业等文档的填写。

你需要：
1. 仔细阅读文档内容，理解所有的问题和要求
2. 为每个问题提供准确、详细的答案
3. 答案应该符合学术规范，内容充实
4. 不要修改原文档中的问题和标题
5. 答案应该插入到合适的位置（问题之后，而不是文档末尾）

你的回答应该是结构化的JSON格式，包含每个需要填写位置的信息。"""
        
        if self.config.custom_prompt:
            base_prompt += f"\n\n用户额外要求：\n{self.config.custom_prompt}"
        
        return base_prompt
    
    def _build_user_prompt(self, document_content: str, structure: dict) -> str:
        """Build the user prompt with document content."""
        prompt = f"""请分析以下文档内容，并为其中的问题和空白处生成合适的答案。

文档内容：
{document_content}

请以JSON格式返回，格式如下：
{{
  "answers": [
    {{
      "paragraph_index": 问题所在段落的索引,
      "question": "问题内容",
      "answer": "你生成的答案",
      "insert_type": "after" 或 "replace"
    }}
  ]
}}

注意：
1. 每个答案都要对应文档中的具体问题
2. 答案要详细、准确
3. 不要创建新的标题
4. 确保答案插入到正确的位置
"""
        
        return prompt
    
    def _parse_ai_response(self, response_text: str, structure: dict) -> dict:
        """Parse the AI response into structured data."""
        import json
        import re
        
        # Try to extract JSON from the response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        # Fallback: create simple structure
        return {
            "answers": [],
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
