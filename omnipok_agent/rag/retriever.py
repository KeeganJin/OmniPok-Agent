"""Retriever for searching and retrieving relevant documents."""
from typing import List, Optional, Dict, Any
from .document import Document
from .vector_store import VectorStore
from .embedding import EmbeddingModel


class Retriever:
    """Retriever that combines vector store and embedding model."""
    
    def __init__(
        self,
        vector_store: VectorStore,
        embedding_model: EmbeddingModel
    ):
        """
        Initialize retriever.
        
        Args:
            vector_store: Vector store instance
            embedding_model: Embedding model instance
        """
        self.vector_store = vector_store
        self.embedding_model = embedding_model
    
    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Retrieve relevant documents for a query.
        
        Args:
            query: Search query
            top_k: Number of documents to retrieve
            filter: Optional metadata filter
            
        Returns:
            List of relevant documents
        """
        # Generate query embedding
        query_embedding = self.embedding_model.embed(query)
        
        # Search in vector store
        documents = self.vector_store.similarity_search(
            query_embedding=query_embedding,
            top_k=top_k,
            filter=filter
        )
        
        return documents
    
    def retrieve_batch(
        self,
        queries: List[str],
        top_k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[List[Document]]:
        """
        Retrieve documents for multiple queries.
        
        Args:
            queries: List of search queries
            top_k: Number of documents to retrieve per query
            filter: Optional metadata filter
            
        Returns:
            List of document lists (one per query)
        """
        # Generate embeddings for all queries
        query_embeddings = self.embedding_model.embed_batch(queries)
        
        # Search for each query
        results = []
        for query_embedding in query_embeddings:
            documents = self.vector_store.similarity_search(
                query_embedding=query_embedding,
                top_k=top_k,
                filter=filter
            )
            results.append(documents)
        
        return results

