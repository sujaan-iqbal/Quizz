import PyPDF2
import re
from typing import List

class PDFProcessor:
    @staticmethod
    def extract_text(pdf_file) -> str:
        """Extract text from PDF file"""
        reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text
    
    @staticmethod
    def chunk_text(text: str, size: int = 600) -> List[str]:
        """Split text into chunks"""
        # Split by paragraphs
        paragraphs = re.split(r'\n\s*\n', text)
        chunks = []
        current_chunk = []
        current_length = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            word_count = len(para.split())
            
            if current_length + word_count <= size:
                current_chunk.append(para)
                current_length += word_count
            else:
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                current_chunk = [para]
                current_length = word_count
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        # Filter chunks that are too short
        return [c for c in chunks if len(c.split()) > 40][:100]
import PyPDF2
import re
from typing import List

class PDFProcessor:
    @staticmethod
    def extract_text(pdf_file) -> str:
        """Extract text from PDF file"""
        reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text
    
    @staticmethod
    def chunk_text(text: str, size: int = 600) -> List[str]:
        """Split text into chunks"""
        # Split by paragraphs
        paragraphs = re.split(r'\n\s*\n', text)
        chunks = []
        current_chunk = []
        current_length = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            word_count = len(para.split())
            
            if current_length + word_count <= size:
                current_chunk.append(para)
                current_length += word_count
            else:
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                current_chunk = [para]
                current_length = word_count
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        # Filter chunks that are too short
        return [c for c in chunks if len(c.split()) > 40][:100]