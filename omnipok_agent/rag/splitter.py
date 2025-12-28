"""Text splitters for chunking documents."""
from typing import List, Optional
from .document import Document


class TextSplitter:
    """Base class for text splitters."""
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: Optional[List[str]] = None
    ):
        """
        Initialize text splitter.
        
        Args:
            chunk_size: Maximum size of each chunk
            chunk_overlap: Number of characters to overlap between chunks
            separators: List of separators to use for splitting
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", " ", ""]
    
    def split_text(self, text: str) -> List[str]:
        """
        Split text into chunks.
        
        Args:
            text: Text to split
            
        Returns:
            List of text chunks
        """
        raise NotImplementedError
    
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split documents into chunks.
        
        Args:
            documents: List of documents to split
            
        Returns:
            List of chunked documents
        """
        chunks = []
        for doc in documents:
            text_chunks = self.split_text(doc.content)
            for i, chunk_text in enumerate(text_chunks):
                chunk_metadata = doc.metadata.copy()
                chunk_metadata.update({
                    "chunk_index": i,
                    "total_chunks": len(text_chunks),
                    "parent_doc_id": doc.id
                })
                chunk = Document(
                    content=chunk_text,
                    metadata=chunk_metadata,
                    id=f"{doc.id}_chunk_{i}"
                )
                chunks.append(chunk)
        return chunks


class RecursiveCharacterTextSplitter(TextSplitter):
    """Recursive character text splitter that tries to split on different separators."""
    
    def split_text(self, text: str) -> List[str]:
        """
        Split text recursively using different separators.
        
        Args:
            text: Text to split
            
        Returns:
            List of text chunks
        """
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        current_text = text
        
        # Try each separator in order
        for separator in self.separators:
            if separator == "":
                # Last resort: split by character
                return self._split_by_char(current_text)
            
            if separator in current_text:
                splits = current_text.split(separator)
                current_chunks = []
                current_chunk = ""
                
                for split in splits:
                    # Add separator back (except for the last split)
                    if current_chunk:
                        current_chunk += separator
                    current_chunk += split
                    
                    if len(current_chunk) >= self.chunk_size:
                        if current_chunks:
                            # Add overlap from previous chunk
                            overlap_text = current_chunk[:self.chunk_overlap]
                            current_chunks[-1] += overlap_text
                            current_chunk = current_chunk[self.chunk_overlap:]
                        current_chunks.append(current_chunk)
                        current_chunk = ""
                
                if current_chunk:
                    current_chunks.append(current_chunk)
                
                # If we got reasonable chunks, use them
                if current_chunks and all(len(c) <= self.chunk_size * 1.5 for c in current_chunks):
                    chunks.extend(current_chunks)
                    break
        
        # If no good split found, fall back to character splitting
        if not chunks:
            chunks = self._split_by_char(text)
        
        return chunks
    
    def _split_by_char(self, text: str) -> List[str]:
        """Split text by character when no good separator is found."""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end]
            
            if end < len(text):
                # Add overlap for next chunk
                overlap_start = max(0, end - self.chunk_overlap)
                overlap_text = text[overlap_start:end]
            
            chunks.append(chunk)
            start = end - self.chunk_overlap if end < len(text) else end
        
        return chunks

