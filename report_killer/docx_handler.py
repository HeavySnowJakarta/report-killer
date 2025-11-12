"""Word document handling utilities using python-docx."""

from typing import List, Dict, Optional, Tuple
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
import re
from pathlib import Path


class InsertionPoint:
    """Represents a point in the document where content should be inserted."""
    
    def __init__(self, para_index: int, point_type: str, description: str):
        self.para_index = para_index
        self.point_type = point_type  # 'question', 'requirement', 'section'
        self.description = description
        self.filled = False
        self.content = []
    
    def __repr__(self):
        status = "✓" if self.filled else "○"
        return f"{status} [{self.point_type}] Para {self.para_index}: {self.description[:50]}..."


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
    
    def analyze_structure(self) -> Dict:
        """Analyze document structure to find all insertion points."""
        if not self.doc:
            self.load()
        
        structure = {
            "paragraphs": [],
            "questions": [],
            "requirements": [],
            "sections": [],
        }
        
        self.insertion_points = []
        
        for idx, para in enumerate(self.doc.paragraphs):
            text = para.text.strip()
            if not text:
                continue
            
            para_info = {
                "index": idx,
                "text": text,
                "style": para.style.name if para.style else "Normal",
            }
            
            # Detect questions (lines ending with ？ or ?)
            if text.endswith("？") or text.endswith("?"):
                para_info["is_question"] = True
                structure["questions"].append(para_info)
                
                # Always mark questions as insertion points
                # We need to check if the answer after it is sufficient
                point = InsertionPoint(idx, "question", text)
                self.insertion_points.append(point)
            
            # Detect numbered requirements like (1), (2), etc.
            if re.match(r'^\(\d+\)\s*$', text):
                para_info["is_requirement"] = True
                structure["requirements"].append(para_info)
                
                # Short numbered items need elaboration
                point = InsertionPoint(idx, "requirement", text)
                self.insertion_points.append(point)
            
            # Detect section requirements like "1、实验报告需要包含以下几个部分"
            elif re.match(r'^\d+[、．]', text) and len(text) < 150:
                para_info["is_section_header"] = True
                structure["requirements"].append(para_info)
                
                # These often need subsection content
                if "需要" in text or "包含" in text or "要求" in text:
                    point = InsertionPoint(idx, "section", text)
                    self.insertion_points.append(point)
            
            # Detect section headers (五、六、etc.)
            if re.match(r'^[一二三四五六七八九十]+、', text):
                para_info["is_section"] = True
                structure["sections"].append(para_info)
            
            structure["paragraphs"].append(para_info)
        
        return structure
    
    def find_all_insertion_points(self) -> List[InsertionPoint]:
        """Find all points where content needs to be inserted."""
        if not self.insertion_points:
            self.analyze_structure()
        
        return self.insertion_points
    
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
    
    def insert_table_after(self, para_index: int, rows: int, cols: int):
        """Insert a table after the specified paragraph."""
        if not self.doc:
            self.load()
        
        # python-docx doesn't have direct insert_table_after
        # We'll add to the end and then move elements
        table = self.doc.add_table(rows=rows, cols=cols)
        table.style = 'Light Grid Accent 1'
        
        return table
    
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
