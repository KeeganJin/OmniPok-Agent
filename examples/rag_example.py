"""Example usage of RAG module."""
import asyncio
import os
from pathlib import Path
from omnipok_agent.rag import (
    KnowledgeBase,
    RAGAgent,
    DocumentLoader,
    RecursiveCharacterTextSplitter,
    OpenAIEmbedding
)
from omnipok_agent.core import RunContext
from omnipok_agent.llm import OmniPokLLM
from omnipok_agent.memory import InMemoryMemory


async def main():
    """Example RAG usage."""
    print("=== RAG Example ===\n")
    
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("Warning: OPENAI_API_KEY not set. RAG requires OpenAI API for embeddings.")
        print("Please set OPENAI_API_KEY environment variable.\n")
        return
    
    # 1. Create a knowledge base
    print("1. Creating knowledge base...")
    kb = KnowledgeBase(
        kb_id="example-kb",
        embedding_model=OpenAIEmbedding(model="text-embedding-3-small"),
        text_splitter=RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=100
        )
    )
    print("✓ Knowledge base created\n")
    
    # 2. Add documents to knowledge base
    print("2. Adding documents to knowledge base...")
    
    # Option 1: Add documents directly
    sample_doc1 = """
    Python is a high-level programming language known for its simplicity and readability.
    It was created by Guido van Rossum and first released in 1991.
    Python supports multiple programming paradigms including procedural, object-oriented, and functional programming.
    """
    sample_doc2 = """
    Machine Learning is a subset of artificial intelligence that focuses on algorithms
    that can learn from data. Common types include supervised learning, unsupervised learning,
    and reinforcement learning.
    """
    
    from omnipok_agent.rag import Document
    kb.add_document(Document(
        content=sample_doc1,
        metadata={"title": "Python Introduction", "topic": "programming"}
    ))
    kb.add_document(Document(
        content=sample_doc2,
        metadata={"title": "Machine Learning Basics", "topic": "AI"}
    ))
    print("✓ Added 2 sample documents\n")
    
    # Option 2: Add from file (if you have text files)
    # kb.add_file("path/to/your/document.txt")
    # kb.add_directory("path/to/documents/", recursive=True)
    
    # 3. Create RAG Agent
    print("3. Creating RAG Agent...")
    agent = RAGAgent(
        agent_id="rag-agent-1",
        knowledge_base=kb,
        llm=OmniPokLLM(),
        memory=InMemoryMemory(),
        top_k=3,
        include_sources=True
    )
    print("✓ RAG Agent created\n")
    
    # 4. Query the knowledge base
    print("4. Querying knowledge base...\n")
    context = RunContext(tenant_id="example", user_id="user1")
    
    queries = [
        "What is Python?",
        "Tell me about machine learning",
        "What programming paradigms does Python support?"
    ]
    
    for query in queries:
        print(f"Q: {query}")
        response = await agent.process(query, context)
        print(f"A: {response}\n")
        print("-" * 80 + "\n")
    
    # 5. Direct knowledge base search
    print("5. Direct knowledge base search...")
    results = kb.search("Python programming", top_k=2)
    print(f"Found {len(results)} relevant documents:")
    for i, doc in enumerate(results, 1):
        print(f"\nDocument {i}:")
        print(f"  Content: {doc.content[:100]}...")
        print(f"  Metadata: {doc.metadata}")
        if "similarity_score" in doc.metadata:
            print(f"  Similarity: {doc.metadata['similarity_score']:.3f}")


if __name__ == "__main__":
    asyncio.run(main())

