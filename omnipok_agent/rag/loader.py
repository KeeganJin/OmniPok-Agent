"""Document loaders for different file types."""
import os
from pathlib import Path
from typing import List, Optional
from .document import Document


class DocumentLoader:
    """Base class for document loaders."""
    
    @staticmethod
    def load(file_path: str) -> List[Document]:
        """
        Load documents from a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            List of Document objects
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Auto-detect loader based on file extension
        suffix = path.suffix.lower()
        
        if suffix == ".txt":
            return TextLoader.load(file_path)
        elif suffix == ".md":
            return MarkdownLoader.load(file_path)
        else:
            raise ValueError(f"Unsupported file type: {suffix}. Supported: .txt, .md")
    
    @staticmethod
    def load_from_directory(directory: str, recursive: bool = True) -> List[Document]:
        """
        Load all supported documents from a directory.
        
        Args:
            directory: Path to directory
            recursive: Whether to search recursively
            
        Returns:
            List of Document objects
        """
        path = Path(directory)
        if not path.is_dir():
            raise ValueError(f"Not a directory: {directory}")
        
        documents = []
        supported_extensions = {".txt", ".md"}
        
        if recursive:
            pattern = "**/*"
        else:
            pattern = "*"
        
        for file_path in path.glob(pattern):
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                try:
                    docs = DocumentLoader.load(str(file_path))
                    documents.extend(docs)
                except Exception as e:
                    # Log error but continue with other files
                    print(f"Error loading {file_path}: {e}")
        
        return documents


class TextLoader:
    """Loader for plain text files."""
    
    @staticmethod
    def load(file_path: str) -> List[Document]:
        """
        Load a text file.
        
        Args:
            file_path: Path to the text file
            
        Returns:
            List containing a single Document
        """
        path = Path(file_path)
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        
        metadata = {
            "source": str(path.absolute()),
            "file_name": path.name,
            "file_type": "text",
            "file_size": path.stat().st_size
        }
        
        return [Document(content=content, metadata=metadata)]


class MarkdownLoader:
    """Loader for Markdown files."""
    
    @staticmethod
    def load(file_path: str) -> List[Document]:
        """
        Load a Markdown file.
        
        Args:
            file_path: Path to the Markdown file
            
        Returns:
            List containing a single Document
        """
        path = Path(file_path)
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        
        metadata = {
            "source": str(path.absolute()),
            "file_name": path.name,
            "file_type": "markdown",
            "file_size": path.stat().st_size
        }
        
        return [Document(content=content, metadata=metadata)]

