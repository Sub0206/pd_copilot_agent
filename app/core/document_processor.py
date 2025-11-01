from pathlib import Path
from typing import Dict
from bs4 import BeautifulSoup
import shutil
import os
from docx import Document
import pdfplumber

DOCS_PATH = os.getenv("PD_DOCS_PATH", "./resource/pd_docs")

class DocumentProcessor:
    def __init__(self):
        self.docs_path = Path(DOCS_PATH)
        self.processed_path = self.docs_path.parent / "processed"
        self.processed_path.mkdir(parents=True, exist_ok=True)
        self.docs_path.mkdir(parents=True, exist_ok=True)
    
    def _read_file(self, file_path: Path) -> str:
        """Read and extract text from various file formats"""
        
        # Handle PDF files
        if file_path.suffix == '.pdf':
            try:
                text = []
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text.append(page_text)
                return '\n\n'.join(text)
            except Exception as e:
                raise Exception(f"Error reading .pdf file: {e}")
        
        # Handle .docx files
        if file_path.suffix == '.docx':
            try:
                doc = Document(file_path)
                # Extract text from all paragraphs
                text = '\n'.join([paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip()])
                return text
            except Exception as e:
                raise Exception(f"Error reading .docx file: {e}")
        
        # Handle HTML files
        if file_path.suffix in ['.html', '.htm']:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            soup = BeautifulSoup(content, 'html.parser')
            return soup.get_text(separator='\n', strip=True)
        
        # Handle text-based files
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _detect_doc_type(self, filename: str, content: str) -> str:
        filename_lower = filename.lower()
        content_sample = content.lower()[:1000]
        
        config_keywords = ['configuration', 'setup', 'config', 'step', 'action', 'workflow']
        feature_keywords = ['feature', 'entity', 'view', 'interface', 'component']
        
        config_score = sum(1 for kw in config_keywords if kw in filename_lower or kw in content_sample)
        feature_score = sum(1 for kw in feature_keywords if kw in filename_lower or kw in content_sample)
        
        if config_score > feature_score:
            return "config"
        elif feature_score > config_score:
            return "feature"
        return "general"
    
    def _move_to_processed(self, file_path: Path):
        dest = self.processed_path / file_path.name
        counter = 1
        while dest.exists():
            dest = self.processed_path / f"{file_path.stem}_{counter}{file_path.suffix}"
            counter += 1
        shutil.move(str(file_path), str(dest))
    
    def has_new_documents(self) -> bool:
        """Check if there are new documents to process"""
        return any(
            f.is_file() and f.suffix in ['.html', '.htm', '.md', '.txt', '.docx', '.pdf']
            for f in self.docs_path.glob("*")
        )
    
    def process_new_documents(self) -> Dict:
        """Process new documents"""
        processed = []
        errors = []
        
        for file_path in self.docs_path.glob("*"):
            if file_path.is_file() and file_path.suffix in ['.html', '.htm', '.md', '.txt', '.docx', '.pdf']:
                try:
                    content = self._read_file(file_path)
                    if not content.strip():
                        continue
                    
                    doc_type = self._detect_doc_type(file_path.name, content)
                    
                    processed.append({
                        "doc_id": file_path.stem,
                        "content": content,
                        "metadata": {
                            "filename": file_path.name,
                            "original_path": str(file_path)
                        },
                        "doc_type": doc_type
                    })
                    
                    self._move_to_processed(file_path)
                    
                except Exception as e:
                    errors.append(f"{file_path.name}: {str(e)}")
        
        return {
            "status": "success",
            "processed": processed,
            "count": len(processed),
            "errors": errors
        }

doc_processor = DocumentProcessor()