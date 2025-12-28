"""SQLite storage backend for long-term memory."""
import sqlite3
import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from ...core.types import Message, AgentState, MessageRole


class SQLiteStore:
    """SQLite storage backend for persistent memory storage."""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize SQLite store.
        
        Args:
            db_path: Path to SQLite database file. If None, uses default location.
        """
        if db_path is None:
            # Default to data directory in project root
            project_root = Path(__file__).parent.parent.parent.parent.parent
            data_dir = project_root / "data"
            data_dir.mkdir(exist_ok=True)
            db_path = str(data_dir / "agent_memory.db")
        
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self) -> None:
        """Initialize database tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    metadata TEXT,
                    importance INTEGER DEFAULT 0,
                    session_id TEXT,
                    name TEXT,
                    tool_calls TEXT,
                    tool_call_id TEXT
                )
            """)
            
            # Memory summaries table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memory_summaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    keywords TEXT,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL
                )
            """)
            
            # Agent states table (for full state persistence)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_states (
                    agent_id TEXT PRIMARY KEY,
                    current_step INTEGER DEFAULT 0,
                    metadata TEXT,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL
                )
            """)
            
            # Create indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_agent_id ON messages(agent_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp ON messages(timestamp)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_importance ON messages(importance)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_session_id ON messages(session_id)
            """)
            
            conn.commit()
    
    def save_message(
        self,
        agent_id: str,
        message: Message,
        importance: int = 0,
        session_id: Optional[str] = None
    ) -> int:
        """
        Save a message to the database.
        
        Args:
            agent_id: Agent identifier
            message: Message to save
            importance: Importance score (0-100, higher is more important)
            session_id: Optional session identifier
            
        Returns:
            Message ID
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Serialize tool_calls if present
            tool_calls_json = None
            if message.tool_calls:
                tool_calls_data = [
                    {
                        "id": tc.id,
                        "name": tc.name,
                        "arguments": tc.arguments
                    }
                    for tc in message.tool_calls
                ]
                tool_calls_json = json.dumps(tool_calls_data)
            
            # Serialize metadata
            metadata_json = None
            if message.metadata:
                metadata_json = json.dumps(message.metadata)
            
            cursor.execute("""
                INSERT INTO messages (
                    agent_id, role, content, timestamp, metadata,
                    importance, session_id, name, tool_calls, tool_call_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                agent_id,
                message.role.value if isinstance(message.role, MessageRole) else str(message.role),
                message.content,
                message.timestamp.isoformat(),
                metadata_json,
                importance,
                session_id,
                message.name,
                tool_calls_json,
                message.tool_call_id
            ))
            
            conn.commit()
            return cursor.lastrowid
    
    def get_messages(
        self,
        agent_id: str,
        limit: Optional[int] = None,
        since: Optional[datetime] = None,
        min_importance: Optional[int] = None
    ) -> List[Message]:
        """
        Retrieve messages from the database.
        
        Args:
            agent_id: Agent identifier
            limit: Maximum number of messages to retrieve
            since: Only retrieve messages after this timestamp
            min_importance: Minimum importance score
            
        Returns:
            List of messages
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = "SELECT * FROM messages WHERE agent_id = ?"
            params = [agent_id]
            
            if since:
                query += " AND timestamp >= ?"
                params.append(since.isoformat())
            
            if min_importance is not None:
                query += " AND importance >= ?"
                params.append(min_importance)
            
            query += " ORDER BY timestamp ASC"
            
            if limit:
                query += " LIMIT ?"
                params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            messages = []
            for row in rows:
                # Deserialize tool_calls
                tool_calls = None
                if row["tool_calls"]:
                    try:
                        tool_calls_data = json.loads(row["tool_calls"])
                        from ...core.types import ToolCall
                        tool_calls = [
                            ToolCall(
                                id=tc["id"],
                                name=tc["name"],
                                arguments=tc["arguments"],
                                timestamp=datetime.fromisoformat(row["timestamp"])
                            )
                            for tc in tool_calls_data
                        ]
                    except (json.JSONDecodeError, KeyError):
                        pass
                
                # Deserialize metadata
                metadata = None
                if row["metadata"]:
                    try:
                        metadata = json.loads(row["metadata"])
                    except json.JSONDecodeError:
                        pass
                
                # Parse role
                role = MessageRole(row["role"])
                
                message = Message(
                    role=role,
                    content=row["content"],
                    name=row["name"],
                    tool_calls=tool_calls,
                    tool_call_id=row["tool_call_id"],
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    metadata=metadata
                )
                messages.append(message)
            
            return messages
    
    def save_state(self, agent_id: str, state: AgentState) -> None:
        """Save agent state to database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            metadata_json = None
            if state.metadata:
                metadata_json = json.dumps(state.metadata)
            
            cursor.execute("""
                INSERT OR REPLACE INTO agent_states (
                    agent_id, current_step, metadata, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                agent_id,
                state.current_step,
                metadata_json,
                state.created_at.isoformat(),
                state.updated_at.isoformat()
            ))
            
            conn.commit()
    
    def load_state(self, agent_id: str) -> Optional[AgentState]:
        """Load agent state from database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM agent_states WHERE agent_id = ?", (agent_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            # Deserialize metadata
            metadata = None
            if row["metadata"]:
                try:
                    metadata = json.loads(row["metadata"])
                except json.JSONDecodeError:
                    pass
            
            # Load messages
            messages = self.get_messages(agent_id)
            
            state = AgentState(
                messages=messages,
                current_step=row["current_step"],
                metadata=metadata or {},
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"])
            )
            
            return state
    
    def clear_agent_memory(self, agent_id: str) -> None:
        """Clear all memory for an agent."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM messages WHERE agent_id = ?", (agent_id,))
            cursor.execute("DELETE FROM agent_states WHERE agent_id = ?", (agent_id,))
            cursor.execute("DELETE FROM memory_summaries WHERE agent_id = ?", (agent_id,))
            conn.commit()
    
    def delete_old_messages(self, agent_id: str, before: datetime) -> int:
        """
        Delete messages older than the specified timestamp.
        
        Args:
            agent_id: Agent identifier
            before: Delete messages before this timestamp
            
        Returns:
            Number of deleted messages
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM messages WHERE agent_id = ? AND timestamp < ?",
                (agent_id, before.isoformat())
            )
            deleted = cursor.rowcount
            conn.commit()
            return deleted

