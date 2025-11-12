"""Word document handling utilities."""

from typing import List, Tuple, Optional, Dict
import zipfile
import tempfile
import shutil
from pathlib import Path
try:
    from lxml import etree as ET
    LXML_AVAILABLE = True
except ImportError:
    from xml.etree import ElementTree as ET
    LXML_AVAILABLE = False
import re


class DocxHandler:
    """Handle reading and writing Word documents using direct XML manipulation."""
    
    # Namespaces for OOXML (both standard and OOXML Transitional)
    NAMESPACES = {
        'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
        'w_alt': 'http://purl.oclc.org/ooxml/wordprocessingml/main',
        'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
        'r_alt': 'http://purl.oclc.org/ooxml/officeDocument/relationships',
    }
    
    def __init__(self, filepath: str):
        """Initialize with a document filepath."""
        self.filepath = filepath
        self.document_xml = None
        self.root = None
        self.body = None
        self.paragraphs = []
        self.namespace = None
        self._temp_dir = None
        
    def load(self):
        """Load the document by extracting and parsing XML."""
        # Extract the docx file
        self._temp_dir = tempfile.mkdtemp()
        
        with zipfile.ZipFile(self.filepath, 'r') as zip_ref:
            zip_ref.extractall(self._temp_dir)
        
        # Load and parse document.xml
        doc_path = Path(self._temp_dir) / 'word' / 'document.xml'
        
        if LXML_AVAILABLE:
            parser = ET.XMLParser(remove_blank_text=False)
            self.document_xml = ET.parse(str(doc_path), parser)
        else:
            self.document_xml = ET.parse(doc_path)
        
        # Detect namespace
        self.root = self.document_xml.getroot()
        self.namespace = self.root.tag.split('}')[0].strip('{')
        
        # Find body element
        ns = {'w': self.namespace}
        self.body = self.root.find('.//w:body', ns)
        
        # Parse paragraphs
        self._parse_paragraphs()
    
    def _parse_paragraphs(self):
        """Parse all paragraphs from the document XML."""
        ns = {'w': self.namespace}
        
        # Find all paragraphs in body
        para_elements = self.body.findall('.//w:p', ns)
        
        self.paragraphs = []
        for elem in para_elements:
            text_parts = []
            for text_elem in elem.findall('.//w:t', ns):
                if text_elem.text:
                    text_parts.append(text_elem.text)
            
            self.paragraphs.append({
                'element': elem,
                'text': ''.join(text_parts),
                'runs': elem.findall('.//w:r', ns)
            })
    
    def get_text_content(self) -> str:
        """Extract all text content from the document."""
        if not self.paragraphs:
            self.load()
        
        content = []
        for para in self.paragraphs:
            if para['text'].strip():
                content.append(para['text'])
        
        return "\n".join(content)
    
    def analyze_structure(self) -> dict:
        """Analyze document structure to understand where to insert content."""
        if not self.paragraphs:
            self.load()
        
        structure = {
            "paragraphs": [],
            "questions": [],
            "blanks": [],
        }
        
        for idx, para in enumerate(self.paragraphs):
            text = para['text'].strip()
            if not text:
                continue
            
            para_info = {
                "index": idx,
                "text": text,
                "is_empty": len(text) == 0,
            }
            
            # Detect questions (lines ending with ？ or ?)
            if text.endswith("？") or text.endswith("?"):
                para_info["is_question"] = True
                structure["questions"].append(para_info)
            
            # Detect blank spaces for filling (multiple spaces or underscores)
            if re.search(r'_{3,}|\s{3,}', text):
                para_info["has_blank"] = True
                structure["blanks"].append(para_info)
            
            structure["paragraphs"].append(para_info)
        
        return structure
    
    def insert_text_after_paragraph(self, para_index: int, text: str):
        """Insert text as a new paragraph after a specific paragraph."""
        if not self.paragraphs:
            self.load()
        
        if para_index >= len(self.paragraphs):
            # Can't insert after non-existent paragraph
            return
        
        # Create a new paragraph element
        ns = {'w': self.namespace}
        
        # Create new paragraph
        if LXML_AVAILABLE:
            new_para = ET.Element(f'{{{self.namespace}}}p', nsmap={'w': self.namespace})
        else:
            new_para = ET.Element(f'{{{self.namespace}}}p')
        
        # Create run
        new_run = ET.SubElement(new_para, f'{{{self.namespace}}}r')
        
        # Create text element
        new_text = ET.SubElement(new_run, f'{{{self.namespace}}}t')
        new_text.text = text
        
        # Preserve whitespace
        if LXML_AVAILABLE:
            new_text.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
        
        # Insert after the target paragraph
        target_elem = self.paragraphs[para_index]['element']
        
        if LXML_AVAILABLE:
            parent = target_elem.getparent()
            index = list(parent).index(target_elem)
            parent.insert(index + 1, new_para)
        else:
            # For ElementTree, we need to find the parent manually
            # Insert in body element at the end for now
            body_paras = list(self.body)
            try:
                index = body_paras.index(target_elem)
                # This is a workaround - we'll insert at the right position
                self.body.insert(index + 1, new_para)
            except ValueError:
                # If we can't find it, append at the end
                self.body.append(new_para)
        
        # Update our paragraphs list
        self._parse_paragraphs()
    
    def replace_text_in_paragraph(self, para_index: int, old_text: str, new_text: str):
        """Replace text within a paragraph."""
        if not self.paragraphs:
            self.load()
        
        if para_index >= len(self.paragraphs):
            return
        
        para = self.paragraphs[para_index]
        if old_text not in para['text']:
            return
        
        # Find the run containing the text and replace it
        ns = {'w': self.namespace}
        for run in para['runs']:
            text_elem = run.find('.//w:t', ns)
            if text_elem is not None and text_elem.text and old_text in text_elem.text:
                text_elem.text = text_elem.text.replace(old_text, new_text)
                break
        
        # Update our paragraphs list
        self._parse_paragraphs()
    
    def save(self, output_path: Optional[str] = None):
        """Save the document."""
        if not self.document_xml:
            raise ValueError("No document loaded")
        
        # Write the modified document.xml back
        doc_path = Path(self._temp_dir) / 'word' / 'document.xml'
        
        if LXML_AVAILABLE:
            self.document_xml.write(
                str(doc_path),
                encoding='utf-8',
                xml_declaration=True,
                pretty_print=False
            )
        else:
            self.document_xml.write(
                doc_path,
                encoding='utf-8',
                xml_declaration=True
            )
        
        # Create new zip file
        save_path = output_path or self.filepath
        
        with zipfile.ZipFile(save_path, 'w', zipfile.ZIP_DEFLATED) as zip_out:
            for root, dirs, files in Path(self._temp_dir).walk():
                for file in files:
                    filepath = root / file
                    arcname = filepath.relative_to(self._temp_dir)
                    zip_out.write(filepath, arcname)
    
    def __del__(self):
        """Clean up temporary directory."""
        if self._temp_dir and Path(self._temp_dir).exists():
            try:
                shutil.rmtree(self._temp_dir)
            except:
                pass
    
    def find_insertion_points(self) -> List[dict]:
        """Find appropriate places to insert content based on document structure."""
        structure = self.analyze_structure()
        insertion_points = []
        
        paragraphs = structure["paragraphs"]
        
        for i, para_info in enumerate(paragraphs):
            # Look for questions
            if para_info.get("is_question"):
                # The answer should go after the question
                insertion_points.append({
                    "type": "after_question",
                    "para_index": para_info["index"],
                    "question": para_info["text"],
                })
            
            # Look for blanks/empty spaces to fill
            elif para_info.get("has_blank"):
                insertion_points.append({
                    "type": "fill_blank",
                    "para_index": para_info["index"],
                    "text": para_info["text"],
                })
        
        return insertion_points
