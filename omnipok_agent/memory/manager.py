"""Memory manager that combines short-term and long-term memory."""
from typing import List, Optional
from datetime import datetime, timedelta
from ..core.types import Message, AgentState
from .base import Memory
from .short_term import ShortTermMemory
from .long_term import LongTermMemory


class MemoryManager(Memory):
    """
    Memory manager that combines short-term and long-term memory.
    
    This manager provides a unified interface for memory operations while
    automatically managing data between short-term (fast, in-memory) and
    long-term (persistent, SQLite) storage.
    
    Strategy:
    - All messages are stored in short-term memory for fast access
    - Important messages are also persisted to long-term memory
    - When loading, combines data from both sources
    - Short-term memory is checked first for recent messages
    """
    
    def __init__(
        self,
        short_term: Optional[ShortTermMemory] = None,
        long_term: Optional[LongTermMemory] = None,
        auto_archive_threshold: int = 50,
        importance_threshold: int = 30
    ):
        """
        Initialize memory manager.
        
        Args:
            short_term: Short-term memory instance. If None, creates a new one.
            long_term: Long-term memory instance. If None, creates a new one.
            auto_archive_threshold: Number of messages in short-term before auto-archiving
            importance_threshold: Minimum importance score to save to long-term (0-100)
        """
        self._short_term = short_term or ShortTermMemory()
        self._long_term = long_term or LongTermMemory()
        self._auto_archive_threshold = auto_archive_threshold
        self._importance_threshold = importance_threshold
    
    def save(self, agent_id: str, state: AgentState) -> None:
        """Save agent state to both short-term and long-term memory."""
        # Save to short-term (always)
        self._short_term.save(agent_id, state)
        
        # Save to long-term (persistent storage)
        self._long_term.save(agent_id, state)
    
    def load(self, agent_id: str) -> Optional[AgentState]:
        """
        Load agent state, combining data from short-term and long-term memory.
        
        Priority: short-term memory (more recent) takes precedence.
        """
        # Try short-term first (most recent)
        short_term_state = self._short_term.load(agent_id)
        
        # Try long-term (persistent)
        long_term_state = self._long_term.load(agent_id)
        
        if short_term_state and long_term_state:
            # Merge: short-term messages are more recent
            # Combine messages, avoiding duplicates
            short_term_message_ids = {id(msg) for msg in short_term_state.messages}
            long_term_messages = [
                msg for msg in long_term_state.messages
                if id(msg) not in short_term_message_ids
            ]
            
            # Combine: short-term first, then long-term
            combined_messages = short_term_state.messages + long_term_messages
            
            # Use short-term state as base, but combine messages
            combined_state = AgentState(
                messages=combined_messages,
                current_step=short_term_state.current_step,
                metadata={**long_term_state.metadata, **short_term_state.metadata},
                created_at=long_term_state.created_at,
                updated_at=short_term_state.updated_at
            )
            return combined_state
        elif short_term_state:
            return short_term_state
        elif long_term_state:
            return long_term_state
        
        return None
    
    def add_message(
        self,
        agent_id: str,
        message: Message,
        importance: Optional[int] = None
    ) -> None:
        """
        Add a message to memory.
        
        Args:
            agent_id: Agent identifier
            message: Message to add
            importance: Importance score (0-100). If None, auto-calculates.
        """
        # Always add to short-term
        self._short_term.add_message(agent_id, message)
        
        # Determine importance if not provided
        if importance is None:
            importance = self._calculate_importance(message)
        
        # Add to long-term if important enough
        if importance >= self._importance_threshold:
            self._long_term.add_message(agent_id, message, importance=importance)
        
        # Auto-archive if short-term is getting full
        short_term_messages = self._short_term.get_messages(agent_id)
        if len(short_term_messages) >= self._auto_archive_threshold:
            self._archive_old_messages(agent_id)
    
    def get_messages(
        self,
        agent_id: str,
        limit: Optional[int] = None,
        since: Optional[datetime] = None,
        min_importance: Optional[int] = None
    ) -> List[Message]:
        """
        Get messages from memory.
        
        Combines messages from both short-term and long-term memory.
        """
        # Get from short-term
        short_term_messages = self._short_term.get_messages(agent_id, limit=None)
        
        # Get from long-term
        long_term_messages = self._long_term.get_messages(
            agent_id,
            limit=None,
            since=since,
            min_importance=min_importance
        )
        
        # Combine and deduplicate
        all_messages = []
        seen_content = set()
        
        # Add short-term messages first (more recent)
        for msg in short_term_messages:
            content_key = (msg.role.value, msg.content, msg.timestamp.isoformat())
            if content_key not in seen_content:
                all_messages.append(msg)
                seen_content.add(content_key)
        
        # Add long-term messages (older)
        for msg in long_term_messages:
            content_key = (msg.role.value, msg.content, msg.timestamp.isoformat())
            if content_key not in seen_content:
                all_messages.append(msg)
                seen_content.add(content_key)
        
        # Sort by timestamp
        all_messages.sort(key=lambda m: m.timestamp)
        
        # Apply limit
        if limit:
            return all_messages[-limit:]
        
        return all_messages
    
    def clear(self, agent_id: str) -> None:
        """Clear agent's memory from both short-term and long-term storage."""
        self._short_term.clear(agent_id)
        self._long_term.clear(agent_id)
    
    def _calculate_importance(self, message: Message) -> int:
        """
        Calculate importance score for a message.
        
        Simple heuristic based on message characteristics.
        Can be overridden for custom importance calculation.
        
        Args:
            message: Message to evaluate
            
        Returns:
            Importance score (0-100)
        """
        importance = 0
        
        # System messages are important
        if message.role.value == "system":
            importance = 80
        
        # User messages are moderately important
        elif message.role.value == "user":
            importance = 50
            
            # Longer messages might be more important
            if len(message.content) > 200:
                importance += 10
        
        # Assistant messages with tool calls are important
        elif message.role.value == "assistant" and message.tool_calls:
            importance = 60
        
        # Check metadata for importance hints
        if message.metadata:
            if message.metadata.get("important", False):
                importance = max(importance, 70)
            if message.metadata.get("importance"):
                importance = max(importance, message.metadata["importance"])
        
        return min(importance, 100)
    
    def _archive_old_messages(self, agent_id: str) -> None:
        """
        Archive old messages from short-term to long-term memory.
        
        Moves messages older than a threshold to long-term storage.
        """
        short_term_messages = self._short_term.get_messages(agent_id)
        
        if not short_term_messages:
            return
        
        # Archive messages older than 1 hour
        cutoff_time = datetime.now() - timedelta(hours=1)
        
        for message in short_term_messages:
            if message.timestamp < cutoff_time:
                importance = self._calculate_importance(message)
                self._long_term.add_message(agent_id, message, importance=importance)
        
        # Note: We don't remove from short-term here to maintain fast access
        # The short-term memory will naturally limit itself
    
    def get_short_term_memory(self) -> ShortTermMemory:
        """Get the short-term memory instance."""
        return self._short_term
    
    def get_long_term_memory(self) -> LongTermMemory:
        """Get the long-term memory instance."""
        return self._long_term

