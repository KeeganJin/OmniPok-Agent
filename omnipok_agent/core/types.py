"""Core type definitions for the agent framework."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from datetime import datetime


class MessageRole(str, Enum):
    """Message roles in a conversation."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class Message:
    """A message in the conversation."""
    role: MessageRole
    content: str
    name: Optional[str] = None
    tool_calls: Optional[List["ToolCall"]] = None
    tool_call_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """初始化后的处理"""
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式（OpenAI API格式）"""
        result = {
            "role": self.role.value if isinstance(self.role, MessageRole) else self.role,
            "content": self.content
        }
        
        # 添加可选字段
        if self.name:
            result["name"] = self.name
        
        if self.tool_calls:
            result["tool_calls"] = [
                {
                    "id": tc.id,
                    "name": tc.name,
                    "arguments": tc.arguments if isinstance(tc.arguments, dict) else tc.arguments
                }
                for tc in self.tool_calls
            ]
        
        if self.tool_call_id:
            result["tool_call_id"] = self.tool_call_id
        
        return result
    
    def __str__(self) -> str:
        """返回消息的字符串表示"""
        role_str = self.role.value if isinstance(self.role, MessageRole) else str(self.role)
        content_preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"[{role_str}] {content_preview}"


@dataclass
class ToolCall:
    """A tool call request."""
    id: str
    name: str
    arguments: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Observation:
    """Result of a tool execution."""
    tool_call_id: str
    content: Union[str, Dict[str, Any]]
    is_error: bool = False
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class AgentState:
    """State of an agent during execution."""
    messages: List[Message] = field(default_factory=list)
    current_step: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def add_message(self, message: Message) -> None:
        """Add a message to the state."""
        self.messages.append(message)
        self.updated_at = datetime.now()

    def get_conversation_history(self) -> List[Message]:
        """Get the conversation history."""
        return self.messages.copy()


class TaskStatus(str, Enum):
    """Status of a task."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """A task to be executed by an agent."""
    id: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    assigned_agent: Optional[str] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

