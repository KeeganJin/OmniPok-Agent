"""Long-term memory implementation using SQLite storage."""
from typing import List, Optional
from datetime import datetime
from ..core.types import Message, AgentState
from .base import Memory
from .storage.sqlite_store import SQLiteStore


class LongTermMemory(Memory):
    """
    Long-term memory implementation using SQLite.
    
    Persists messages and agent states to disk for permanent storage.
    Suitable for important information that should persist across sessions.
    """
    
    def __init__(self, db_path: Optional[str] = None, default_importance: int = 0):
        """
        Initialize long-term memory.
        
        Args:
            db_path: Path to SQLite database file. If None, uses default location.
            default_importance: Default importance score for messages (0-100)
        """
        self._store = SQLiteStore(db_path)
        self._default_importance = default_importance
        self._current_session_id: Optional[str] = None
    
    def set_session_id(self, session_id: str) -> None:
        """Set the current session ID for message tracking."""
        self._current_session_id = session_id
    
    def save(self, agent_id: str, state: AgentState) -> None:
        """Save agent state to long-term storage."""
        self._store.save_state(agent_id, state)
        
        # Also save all messages
        for message in state.messages:
            self._store.save_message(
                agent_id=agent_id,
                message=message,
                importance=self._default_importance,
                session_id=self._current_session_id
            )
    
    def load(self, agent_id: str) -> Optional[AgentState]:
        """Load agent state from long-term storage."""
        return self._store.load_state(agent_id)
    
    def add_message(
        self,
        agent_id: str,
        message: Message,
        importance: Optional[int] = None
    ) -> None:
        """
        Add a message to long-term memory.
        
        Args:
            agent_id: Agent identifier
            message: Message to add
            importance: Importance score (0-100). If None, uses default.
        """
        if importance is None:
            importance = self._default_importance
        
        self._store.save_message(
            agent_id=agent_id,
            message=message,
            importance=importance,
            session_id=self._current_session_id
        )
    
    def get_messages(
        self,
        agent_id: str,
        limit: Optional[int] = None,
        since: Optional[datetime] = None,
        min_importance: Optional[int] = None
    ) -> List[Message]:
        """
        Get messages from long-term memory.
        
        Args:
            agent_id: Agent identifier
            limit: Maximum number of messages to retrieve
            since: Only retrieve messages after this timestamp
            min_importance: Minimum importance score
            
        Returns:
            List of messages
        """
        return self._store.get_messages(
            agent_id=agent_id,
            limit=limit,
            since=since,
            min_importance=min_importance
        )
    
    def clear(self, agent_id: str) -> None:
        """Clear agent's long-term memory."""
        self._store.clear_agent_memory(agent_id)
    
    def delete_old_messages(self, agent_id: str, before: datetime) -> int:
        """
        Delete old messages before a certain timestamp.
        
        Args:
            agent_id: Agent identifier
            before: Delete messages before this timestamp
            
        Returns:
            Number of deleted messages
        """
        return self._store.delete_old_messages(agent_id, before)

