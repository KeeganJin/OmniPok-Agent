"""Short-term memory implementation using in-memory storage."""
from typing import List, Optional
from collections import deque
from ..core.types import Message, AgentState
from .base import Memory


class ShortTermMemory(Memory):
    """
    Short-term memory implementation.
    
    Stores messages in memory for the current session.
    Automatically limits the number of stored messages to prevent memory overflow.
    """
    
    def __init__(self, max_messages: int = 100):
        """
        Initialize short-term memory.
        
        Args:
            max_messages: Maximum number of messages to store per agent (default: 100)
        """
        self._storage: dict[str, AgentState] = {}
        self._max_messages = max_messages
    
    def save(self, agent_id: str, state: AgentState) -> None:
        """Save agent state."""
        # Limit the number of messages
        if len(state.messages) > self._max_messages:
            # Keep only the most recent messages
            state.messages = state.messages[-self._max_messages:]
        
        self._storage[agent_id] = state
    
    def load(self, agent_id: str) -> Optional[AgentState]:
        """Load agent state."""
        return self._storage.get(agent_id)
    
    def add_message(self, agent_id: str, message: Message) -> None:
        """Add a message to agent's memory."""
        if agent_id not in self._storage:
            self._storage[agent_id] = AgentState()
        
        state = self._storage[agent_id]
        state.add_message(message)
        
        # Enforce message limit
        if len(state.messages) > self._max_messages:
            # Remove oldest messages
            state.messages = state.messages[-self._max_messages:]
    
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
    
    def get_all_agent_ids(self) -> List[str]:
        """Get all agent IDs that have memory stored."""
        return list(self._storage.keys())

