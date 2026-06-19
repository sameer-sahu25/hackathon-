from typing import List
import re


class SmartChunker:
    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 150):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = ["\n\n", "\n", ". ", "! ", "? ", " "]

    def _preserve_special_tokens(self, text: str) -> tuple[str, dict]:
        phone_pattern = r'\b(?:\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
        url_pattern = r'https?://[^\s]+'
        
        replacements = {}
        count = 0
        
        def replace_phone(match):
            nonlocal count
            token = f"__PHONE_{count}__"
            replacements[token] = match.group(0)
            count += 1
            return token
        
        def replace_url(match):
            nonlocal count
            token = f"__URL_{count}__"
            replacements[token] = match.group(0)
            count += 1
            return token
        
        text = re.sub(phone_pattern, replace_phone, text)
        text = re.sub(url_pattern, replace_url, text)
        
        return text, replacements

    def _restore_special_tokens(self, text: str, replacements: dict) -> str:
        for token, original in replacements.items():
            text = text.replace(token, original)
        return text

    def _split_text(self, text: str) -> List[str]:
        chunks = []
        current_chunk = []
        current_length = 0
        
        words = text.split()
        for word in words:
            word_length = len(word) + 1
            
            if current_length + word_length > self.chunk_size and current_chunk:
                chunks.append(" ".join(current_chunk))
                
                overlap_size = int(self.chunk_overlap / 5)
                current_chunk = current_chunk[-overlap_size:] if overlap_size > 0 else []
                current_length = sum(len(w) + 1 for w in current_chunk)
            
            current_chunk.append(word)
            current_length += word_length
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks

    def chunk(self, text: str, metadata: dict = None) -> List[dict]:
        text, replacements = self._preserve_special_tokens(text)
        raw_chunks = self._split_text(text)
        
        chunks = []
        for i, chunk_text in enumerate(raw_chunks):
            chunk_text = self._restore_special_tokens(chunk_text, replacements)
            chunk_metadata = metadata.copy() if metadata else {}
            chunk_metadata["chunk_index"] = i
            chunk_metadata["total_chunks"] = len(raw_chunks)
            chunks.append({
                "id": f"{metadata.get('source', 'unknown')}_{i}" if metadata else f"chunk_{i}",
                "text": chunk_text,
                "metadata": chunk_metadata
            })
        
        return chunks
