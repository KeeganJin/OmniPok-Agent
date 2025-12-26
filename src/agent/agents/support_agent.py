"""Support agent implementation."""
from typing import Optional
from ..agents.base_agent_impl import BaseAgentImpl
from ..core.tool_registry import ToolRegistry
from ..core.memory import Memory
from ..core.llm import OmniPokLLM


class SupportAgent(BaseAgentImpl):
    """A specialized agent for customer support tasks."""
    
    def __init__(
        self,
        agent_id: str,
        llm: Optional[OmniPokLLM] = None,
        memory: Optional[Memory] = None,
        tool_registry: Optional[ToolRegistry] = None
    ):
        """
        Initialize Support Agent.
        
        Args:
            agent_id: Unique agent identifier
            llm: OmniPokLLM instance (if None, will auto-detect)
            memory: Memory backend
            tool_registry: Tool registry
        """
        system_prompt = """You are a helpful customer support agent. 
        Your goal is to assist users with their questions and problems in a friendly and professional manner.
        Always be polite, patient, and try to provide clear and actionable solutions."""
        
        super().__init__(
            agent_id=agent_id,
            name="Support Agent",
            llm=llm,
            memory=memory,
            tool_registry=tool_registry,
            system_prompt=system_prompt
        )

