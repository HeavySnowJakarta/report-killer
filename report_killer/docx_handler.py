"""Word document handling utilities using python-docx."""

from typing import List, Dict, Optional, Tuple
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
import re
from pathlib import Path


class InsertionPoint:
    """Represents a point in the document where content should be inserted."""
    
    def __init__(self, para_index: int, description: str, context_before: str = "", context_after: str = ""):
        self.para_index = para_index
        self.description = description
        self.context_before = context_before
        self.context_after = context_after
        self.filled = False
        self.content = []
    
    def __repr__(self):
        status = "✓" if self.filled else "○"
        return f"{status} Para {self.para_index}: {self.description[:50]}..."


class DocxHandler:
    """Handle reading and writing Word documents using python-docx."""
    
    def __init__(self, filepath: str):
        """Initialize with a document filepath."""
        self.filepath = Path(filepath)
        self.doc = None
        self.insertion_points: List[InsertionPoint] = []
        
    def load(self):
        """Load the document."""
        self.doc = Document(self.filepath)
        
    def get_text_content(self) -> str:
        """Extract all text content from the document."""
        if not self.doc:
            self.load()
        
        content = []
        for para in self.doc.paragraphs:
            if para.text.strip():
                content.append(para.text)
        
        # Also extract text from tables
        for table in self.doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    if cell.text.strip():
                        content.append(cell.text)
        
        return "\n".join(content)
    
    def get_paragraphs_with_indices(self) -> List[Tuple[int, str]]:
        """Get all paragraphs with their indices."""
        if not self.doc:
            self.load()
        
        result = []
        for idx, para in enumerate(self.doc.paragraphs):
            text = para.text.strip()
            if text:
                result.append((idx, text))
        
        return result
    
    def get_context_around_index(self, para_index: int, before: int = 5, after: int = 5) -> Tuple[str, str]:
        """Get context before and after a paragraph index."""
        if not self.doc:
            self.load()
        
        before_text = []
        after_text = []
        
        for i in range(max(0, para_index - before), para_index):
            if i < len(self.doc.paragraphs):
                text = self.doc.paragraphs[i].text.strip()
                if text:
                    before_text.append(text)
        
        for i in range(para_index + 1, min(len(self.doc.paragraphs), para_index + after + 1)):
            text = self.doc.paragraphs[i].text.strip()
            if text:
                after_text.append(text)
        
        return "\n".join(before_text), "\n".join(after_text)
    
    def set_insertion_points(self, points: List[InsertionPoint]):
        """Set the insertion points from LLM analysis."""
        self.insertion_points = points
    
    def insert_paragraph_after(self, para_index: int, text: str, style: Optional[str] = None):
        """Insert a new paragraph after the specified paragraph."""
        if not self.doc:
            self.load()
        
        if para_index >= len(self.doc.paragraphs):
            # Append at end
            new_para = self.doc.add_paragraph(text)
        else:
            # Get the paragraph to insert after
            target_para = self.doc.paragraphs[para_index]
            
            # Insert after by getting the parent element and inserting
            new_para = target_para.insert_paragraph_before(text)
            
            # Move it to after the target
            target_para._element.addnext(new_para._element)
        
        if style:
            new_para.style = style
        
        return new_para
    
    def insert_content_at_point(self, point: InsertionPoint, content: List[str]):
        """Insert content at the specified insertion point."""
        if not self.doc:
            self.load()
        
        # Insert each piece of content as a new paragraph
        for i, text in enumerate(content):
            # Insert after the insertion point paragraph
            insert_index = point.para_index + i
            self.insert_paragraph_after(insert_index, text)
        
        point.filled = True
        point.content = content
    
    def insert_code_block(self, para_index: int, code: str, language: str = ""):
        """Insert a code block with proper formatting."""
        if not self.doc:
            self.load()
        
        # Add code as a paragraph with monospace font
        code_para = self.insert_paragraph_after(para_index, code)
        
        # Format as code
        for run in code_para.runs:
            run.font.name = 'Consolas'
            run.font.size = Pt(9)
        
        # Optionally add language label
        if language:
            label_para = self.insert_paragraph_after(para_index, f"[{language}]")
            for run in label_para.runs:
                run.font.italic = True
                run.font.size = Pt(9)
    
    def save(self, output_path: Optional[str] = None):
        """Save the document."""
        if not self.doc:
            raise ValueError("No document loaded")
        
        save_path = output_path or str(self.filepath)
        self.doc.save(save_path)
    
    def get_completion_status(self) -> Dict:
        """Get status of all insertion points."""
        total = len(self.insertion_points)
        filled = sum(1 for p in self.insertion_points if p.filled)
        
        return {
            "total": total,
            "filled": filled,
            "remaining": total - filled,
            "completion_rate": filled / total if total > 0 else 0,
            "points": self.insertion_points,
        }
