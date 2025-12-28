"""Text processing agent implementation."""
from typing import Optional
from ..core.base import BaseAgent
from ..tools.registry import ToolRegistry
from ..memory.base import Memory
from ..llm.omnipok_llm import OmniPokLLM


class TextAgent(BaseAgent):
    """
    Specialized agent for text processing tasks.
    
    This agent is optimized for:
    - Text summarization
    - Text translation
    - Text analysis
    - Content generation
    """
    
    def __init__(
        self,
        agent_id: str,
        llm: Optional[OmniPokLLM] = None,
        memory: Optional[Memory] = None,
        tool_registry: Optional[ToolRegistry] = None
    ):
        """
        Initialize Text Agent.
        
        Args:
            agent_id: Unique agent identifier
            llm: OmniPokLLM instance (if None, will auto-detect)
            memory: Memory backend
            tool_registry: Tool registry
        """
        system_prompt = """You are a specialized text processing agent. 
        Your expertise includes:
        - Summarizing long texts concisely
        - Translating between languages accurately
        - Analyzing text content and extracting key information
        - Generating high-quality written content
        
        Always provide clear, well-structured, and accurate text processing results."""
        
        super().__init__(
            agent_id=agent_id,
            name="Text Agent",
            llm=llm,
            memory=memory,
            tool_registry=tool_registry,
            system_prompt=system_prompt
        )

