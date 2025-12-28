"""Knowledge base manager for RAG."""
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from .document import Document
from .loader import DocumentLoader
from .splitter import TextSplitter, RecursiveCharacterTextSplitter
from .embedding import EmbeddingModel, OpenAIEmbedding
from .vector_store import VectorStore, ChromaVectorStore
from .retriever import Retriever


class KnowledgeBase:
    """Manages a knowledge base with documents, embeddings, and retrieval."""
    
    def __init__(
        self,
        kb_id: str,
        embedding_model: Optional[EmbeddingModel] = None,
        text_splitter: Optional[TextSplitter] = None,
        persist_directory: Optional[str] = None,
        vector_store: Optional[VectorStore] = None
    ):
        """
        Initialize knowledge base.
        
        Args:
            kb_id: Unique identifier for the knowledge base
            embedding_model: Embedding model (if None, creates OpenAIEmbedding)
            text_splitter: Text splitter (if None, creates RecursiveCharacterTextSplitter)
            persist_directory: Directory to persist vector store data
            vector_store: Vector store instance (if None, creates ChromaVectorStore)
        """
        self.kb_id = kb_id
        
        # Initialize components
        self.embedding_model = embedding_model or OpenAIEmbedding()
        self.text_splitter = text_splitter or RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        
        # Initialize vector store
        if vector_store:
            self.vector_store = vector_store
        else:
            persist_path = persist_directory or os.path.join(
                os.getcwd(), "data", "chroma", kb_id
            )
            os.makedirs(persist_path, exist_ok=True)
            self.vector_store = ChromaVectorStore(
                collection_name=kb_id,
                persist_directory=persist_path,
                embedding_dimension=self.embedding_model.dimension
            )
        
        # Initialize retriever
        self.retriever = Retriever(
            vector_store=self.vector_store,
            embedding_model=self.embedding_model
        )
    
    def add_document(self, document: Document) -> None:
        """
        Add a single document to the knowledge base.
        
        Args:
            document: Document to add
        """
        self.add_documents([document])
    
    def add_documents(self, documents: List[Document]) -> None:
        """
        Add multiple documents to the knowledge base.
        
        Documents are automatically split, embedded, and stored.
        
        Args:
            documents: List of documents to add
        """
        if not documents:
            return
        
        # Split documents into chunks
        chunks = self.text_splitter.split_documents(documents)
        
        # Generate embeddings
        texts = [chunk.content for chunk in chunks]
        embeddings = self.embedding_model.embed_batch(texts)
        
        # Store in vector store
        self.vector_store.add_documents(chunks, embeddings)
    
    def add_file(self, file_path: str) -> List[Document]:
        """
        Load and add a file to the knowledge base.
        
        Args:
            file_path: Path to the file
            
        Returns:
            List of documents that were added
        """
        documents = DocumentLoader.load(file_path)
        self.add_documents(documents)
        return documents
    
    def add_directory(self, directory: str, recursive: bool = True) -> List[Document]:
        """
        Load and add all supported files from a directory.
        
        Args:
            directory: Path to directory
            recursive: Whether to search recursively
            
        Returns:
            List of documents that were added
        """
        documents = DocumentLoader.load_from_directory(directory, recursive=recursive)
        self.add_documents(documents)
        return documents
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Search the knowledge base for relevant documents.
        
        Args:
            query: Search query
            top_k: Number of results to return
            filter: Optional metadata filter
            
        Returns:
            List of relevant documents
        """
        return self.retriever.retrieve(query, top_k=top_k, filter=filter)
    
    def delete_documents(self, document_ids: List[str]) -> None:
        """
        Delete documents from the knowledge base.
        
        Args:
            document_ids: List of document IDs to delete
        """
        self.vector_store.delete(document_ids)
    
    def get_all_document_ids(self) -> List[str]:
        """
        Get all document IDs in the knowledge base.
        
        Returns:
            List of document IDs
        """
        if hasattr(self.vector_store, "get_all_document_ids"):
            return self.vector_store.get_all_document_ids()
        return []
    
    def clear(self) -> None:
        """Clear all documents from the knowledge base."""
        document_ids = self.get_all_document_ids()
        if document_ids:
            self.delete_documents(document_ids)

