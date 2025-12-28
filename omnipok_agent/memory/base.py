"""Base Memory interface."""
from abc import ABC, abstractmethod
from typing import List, Optional
from ..core.types import Message, AgentState


class Memory(ABC):
    """Abstract interface for agent memory."""
    
    @abstractmethod
    def save(self, agent_id: str, state: AgentState) -> None:
        """Save agent state."""
        pass
    
    @abstractmethod
    def load(self, agent_id: str) -> Optional[AgentState]:
        """Load agent state."""
        pass
    
    @abstractmethod
    def add_message(self, agent_id: str, message: Message) -> None:
        """Add a message to agent's memory."""
        pass
    
    @abstractmethod
    def get_messages(self, agent_id: str, limit: Optional[int] = None) -> List[Message]:
        """Get messages from agent's memory."""
        pass
    
    @abstractmethod
    def clear(self, agent_id: str) -> None:
        """Clear agent's memory."""
        pass

