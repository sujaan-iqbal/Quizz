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
    def chunk_text(
        text: str, 
        size: int = 150, 
        overlap: int = 50
    ) -> List[str]:
        """
        Split text into overlapping chunks for better coverage.
        
        Args:
            text: Input text to chunk
            size: Target chunk size in words (reduced from 600)
            overlap: Number of overlapping words between chunks
        
        Returns:
            List of text chunks
        """
        # Split by paragraphs
        paragraphs = re.split(r'\n\s*\n', text)
        
        # First pass: create initial chunks by paragraphs
        initial_chunks = []
        current_chunk = []
        current_length = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            word_count = len(para.split())
            
            # If a single paragraph exceeds chunk size, split it further
            if word_count > size:
                # Save current chunk if exists
                if current_chunk:
                    initial_chunks.append(" ".join(current_chunk))
                    current_chunk = []
                    current_length = 0
                
                # Split large paragraph into sentences
                sentences = re.split(r'(?<=[.!?])\s+', para)
                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue
                    
                    sent_word_count = len(sentence.split())
                    
                    if current_length + sent_word_count <= size:
                        current_chunk.append(sentence)
                        current_length += sent_word_count
                    else:
                        if current_chunk:
                            initial_chunks.append(" ".join(current_chunk))
                        current_chunk = [sentence]
                        current_length = sent_word_count
                
                continue  # Move to next paragraph
            
            # Normal paragraph handling
            if current_length + word_count <= size:
                current_chunk.append(para)
                current_length += word_count
            else:
                if current_chunk:
                    initial_chunks.append(" ".join(current_chunk))
                current_chunk = [para]
                current_length = word_count
        
        # Don't forget the last chunk
        if current_chunk:
            initial_chunks.append(" ".join(current_chunk))
        
        # Second pass: create overlapping chunks
        overlapping_chunks = []
        
        for i, chunk in enumerate(initial_chunks):
            words = chunk.split()
            
            # If chunk is too small, merge with previous or next
            if len(words) < 20:
                continue
            
            # Add base chunk
            overlapping_chunks.append(chunk)
            
            # Create overlap with next chunk if available
            if overlap > 0 and i < len(initial_chunks) - 1:
                next_words = initial_chunks[i + 1].split()
                
                # Take end of current + start of next
                if len(words) > overlap and len(next_words) > overlap:
                    overlap_chunk = (
                        " ".join(words[-overlap:]) + 
                        " " + 
                        " ".join(next_words[:size - overlap])
                    )
                    overlapping_chunks.append(overlap_chunk)
        
        # Debug output
        print(f"📊 Chunking summary:")
        print(f"   Total paragraphs: {len(paragraphs)}")
        print(f"   Initial chunks: {len(initial_chunks)}")
        print(f"   Overlapping chunks: {len(overlapping_chunks)}")
        for i, chunk in enumerate(overlapping_chunks[:5]):
            print(f"   Chunk {i+1}: {len(chunk.split())} words")
        
        # Filter and limit
        return [
            c for c in overlapping_chunks 
            if len(c.split()) > 20
        ][:200]