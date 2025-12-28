"""Vector store implementations for storing and retrieving document embeddings."""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from .document import Document


class VectorStore(ABC):
    """Abstract base class for vector stores."""
    
    @abstractmethod
    def add_documents(self, documents: List[Document], embeddings: List[List[float]]) -> None:
        """
        Add documents with their embeddings to the vector store.
        
        Args:
            documents: List of documents to add
            embeddings: List of embedding vectors (one per document)
        """
        pass
    
    @abstractmethod
    def similarity_search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Search for similar documents.
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            filter: Optional metadata filter
            
        Returns:
            List of similar documents
        """
        pass
    
    @abstractmethod
    def delete(self, document_ids: List[str]) -> None:
        """
        Delete documents by IDs.
        
        Args:
            document_ids: List of document IDs to delete
        """
        pass
    
    @abstractmethod
    def get_collection_name(self) -> str:
        """Get the name of the collection/knowledge base."""
        pass


class ChromaVectorStore(VectorStore):
    """ChromaDB vector store implementation."""
    
    def __init__(
        self,
        collection_name: str,
        persist_directory: Optional[str] = None,
        embedding_dimension: int = 1536
    ):
        """
        Initialize ChromaDB vector store.
        
        Args:
            collection_name: Name of the collection (knowledge base)
            persist_directory: Directory to persist data (if None, uses in-memory)
            embedding_dimension: Dimension of embedding vectors
        """
        try:
            import chromadb
            from chromadb.config import Settings
        except ImportError:
            raise ImportError(
                "ChromaDB is required. Install it with: pip install chromadb"
            )
        
        self.collection_name = collection_name
        self.embedding_dimension = embedding_dimension
        
        # Initialize ChromaDB client
        if persist_directory:
            self.client = chromadb.PersistentClient(path=persist_directory)
        else:
            self.client = chromadb.Client()
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(name=collection_name)
        except Exception:
            # Collection doesn't exist, create it
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}  # Use cosine similarity
            )
    
    def add_documents(self, documents: List[Document], embeddings: List[List[float]]) -> None:
        """Add documents with embeddings to ChromaDB."""
        if len(documents) != len(embeddings):
            raise ValueError("Number of documents must match number of embeddings")
        
        ids = [doc.id for doc in documents]
        texts = [doc.content for doc in documents]
        metadatas = [doc.metadata for doc in documents]
        
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )
    
    def similarity_search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """Search for similar documents in ChromaDB."""
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filter
        )
        
        documents = []
        if results["ids"] and len(results["ids"][0]) > 0:
            for i in range(len(results["ids"][0])):
                doc_id = results["ids"][0][i]
                content = results["documents"][0][i]
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                distance = results["distances"][0][i] if results["distances"] else None
                
                # Add similarity score to metadata
                if distance is not None:
                    metadata["similarity_score"] = 1 - distance  # Convert distance to similarity
                
                doc = Document(
                    id=doc_id,
                    content=content,
                    metadata=metadata
                )
                documents.append(doc)
        
        return documents
    
    def delete(self, document_ids: List[str]) -> None:
        """Delete documents from ChromaDB."""
        if document_ids:
            self.collection.delete(ids=document_ids)
    
    def get_collection_name(self) -> str:
        """Get the collection name."""
        return self.collection_name
    
    def get_all_document_ids(self) -> List[str]:
        """Get all document IDs in the collection."""
        results = self.collection.get()
        return results["ids"] if results["ids"] else []

