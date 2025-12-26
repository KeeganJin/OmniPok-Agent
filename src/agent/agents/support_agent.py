"""Support agent implementation."""
from typing import Optional, Any
from ..agents.base_agent_impl import BaseAgentImpl
from ..core.tool_registry import ToolRegistry
from ..core.memory import Memory


class SupportAgent(BaseAgentImpl):
    """A specialized agent for customer support tasks."""
    
    def __init__(
        self,
        agent_id: str,
        llm_client: Any,
        memory: Optional[Memory] = None,
        tool_registry: Optional[ToolRegistry] = None
    ):
        system_prompt = """You are a helpful customer support agent. 
        Your goal is to assist users with their questions and problems in a friendly and professional manner.
        Always be polite, patient, and try to provide clear and actionable solutions."""
        
        super().__init__(
            agent_id=agent_id,
            name="Support Agent",
            llm_client=llm_client,
            memory=memory,
            tool_registry=tool_registry,
            system_prompt=system_prompt
        )

