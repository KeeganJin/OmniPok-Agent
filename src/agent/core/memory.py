"""Memory interface for agent state persistence."""
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


class InMemoryMemory(Memory):
    """In-memory implementation of Memory."""
    
    def __init__(self):
        self._storage: dict[str, AgentState] = {}
    
    def save(self, agent_id: str, state: AgentState) -> None:
        """Save agent state."""
        self._storage[agent_id] = state
    
    def load(self, agent_id: str) -> Optional[AgentState]:
        """Load agent state."""
        return self._storage.get(agent_id)
    
    def add_message(self, agent_id: str, message: Message) -> None:
        """Add a message to agent's memory."""
        if agent_id not in self._storage:
            self._storage[agent_id] = AgentState()
        self._storage[agent_id].add_message(message)
    
    def get_messages(self, agent_id: str, limit: Optional[int] = None) -> List[Message]:
        """Get messages from agent's memory."""
        if agent_id not in self._storage:
            return []
        messages = self._storage[agent_id].get_conversation_history()
        if limit:
            return messages[-limit:]
        return messages
    
    def clear(self, agent_id: str) -> None:
        """Clear agent's memory."""
        if agent_id in self._storage:
            del self._storage[agent_id]

