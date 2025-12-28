"""RAG Agent implementation."""
from typing import Optional, List
from ..core.base import BaseAgent
from ..core.context import RunContext
from ..tools.registry import ToolRegistry
from ..memory.base import Memory
from ..llm.omnipok_llm import OmniPokLLM
from .knowledge_base import KnowledgeBase


class RAGAgent(BaseAgent):
    """
    RAG (Retrieval-Augmented Generation) Agent.
    
    This agent enhances responses by retrieving relevant documents from a knowledge base
    and using them as context when generating answers.
    """
    
    def __init__(
        self,
        agent_id: str,
        knowledge_base: KnowledgeBase,
        llm: Optional[OmniPokLLM] = None,
        memory: Optional[Memory] = None,
        tool_registry: Optional[ToolRegistry] = None,
        top_k: int = 5,
        include_sources: bool = True
    ):
        """
        Initialize RAG Agent.
        
        Args:
            agent_id: Unique agent identifier
            knowledge_base: KnowledgeBase instance to use for retrieval
            llm: OmniPokLLM instance (if None, will auto-detect)
            memory: Memory backend
            tool_registry: Tool registry
            top_k: Number of documents to retrieve for each query
            include_sources: Whether to include source information in responses
        """
        system_prompt = """You are a helpful AI assistant with access to a knowledge base.
        When answering questions, use the provided context from the knowledge base to give accurate and informative answers.
        If the context doesn't contain relevant information, say so clearly.
        Always cite your sources when using information from the knowledge base."""
        
        super().__init__(
            agent_id=agent_id,
            name="RAG Agent",
            llm=llm,
            memory=memory,
            tool_registry=tool_registry,
            system_prompt=system_prompt
        )
        
        self.knowledge_base = knowledge_base
        self.top_k = top_k
        self.include_sources = include_sources
    
    async def process(self, message: str, context: RunContext) -> str:
        """
        Process a message with RAG enhancement.
        
        The process:
        1. Retrieve relevant documents from knowledge base
        2. Build enhanced prompt with context
        3. Generate response using LLM
        4. Return response with optional source citations
        
        Args:
            message: The user message/query
            context: The run context
            
        Returns:
            The agent's enhanced response
        """
        context.start()
        context.increment_step()
        
        try:
            # Add user message
            from ..core.types import Message, MessageRole
            user_msg = Message(role=MessageRole.USER, content=message)
            self.add_message(user_msg)
            
            # Retrieve relevant documents from knowledge base
            retrieved_docs = self.knowledge_base.search(message, top_k=self.top_k)
            
            # Build enhanced prompt with context
            enhanced_prompt = self._build_enhanced_prompt(message, retrieved_docs)
            
            # Build messages for LLM
            messages = self._build_messages()
            # Replace the last user message with the enhanced prompt
            if messages and messages[-1]["role"] == "user":
                messages[-1]["content"] = enhanced_prompt
            
            # Get available tools (only if tool_registry is configured)
            available_tools = []
            if self.tool_registry:
                available_tools = self.get_available_tools(
                    user_permissions=context.metadata.get("permissions", [])
                )
            
            # Call LLM
            response = await self._call_llm(messages, available_tools if available_tools else None)
            
            # Update context with usage if available
            if response.get("usage"):
                usage = response["usage"]
                tokens = usage.get("total_tokens", 0)
                cost = tokens * 0.000002  # Rough estimate
                context.add_cost(tokens, cost)
            
            # Handle tool calls if any
            final_response = await self._handle_response(response, context)
            
            # Add source citations if requested
            if self.include_sources and retrieved_docs:
                final_response = self._add_source_citations(final_response, retrieved_docs)
            
            # Add assistant message
            assistant_msg = Message(
                role=MessageRole.ASSISTANT,
                content=final_response
            )
            self.add_message(assistant_msg)
            
            # Save state
            self.save_state()
            
            return final_response
            
        finally:
            context.end()
    
    def _build_enhanced_prompt(self, query: str, documents: List) -> str:
        """
        Build an enhanced prompt with retrieved context.
        
        Args:
            query: Original user query
            documents: Retrieved documents
            
        Returns:
            Enhanced prompt string
        """
        if not documents:
            return query
        
        # Build context from retrieved documents
        context_parts = []
        for i, doc in enumerate(documents, 1):
            source = doc.metadata.get("source", "Unknown")
            chunk_index = doc.metadata.get("chunk_index", "")
            context_parts.append(
                f"[Document {i} - Source: {source}"
                f"{f', Chunk {chunk_index}' if chunk_index != '' else ''}]\n"
                f"{doc.content}\n"
            )
        
        context_text = "\n".join(context_parts)
        
        # Build enhanced prompt
        enhanced_prompt = f"""Use the following context from the knowledge base to answer the question.
If the context doesn't contain relevant information, say so clearly.

Context:
{context_text}

Question: {query}

Answer:"""
        
        return enhanced_prompt
    
    def _add_source_citations(self, response: str, documents: List) -> str:
        """
        Add source citations to the response.
        
        Args:
            response: Original response
            documents: Retrieved documents used
            
        Returns:
            Response with source citations
        """
        if not documents:
            return response
        
        sources = []
        for doc in documents:
            source = doc.metadata.get("source", "Unknown")
            file_name = doc.metadata.get("file_name", "")
            if file_name:
                source = file_name
            if source not in sources:
                sources.append(source)
        
        if sources:
            citations = "\n\nSources:\n" + "\n".join(f"- {source}" for source in sources)
            return response + citations
        
        return response

