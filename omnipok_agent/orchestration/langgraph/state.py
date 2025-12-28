"""State definitions for LangGraph orchestration."""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from ...core.base import BaseAgent
from ...core.context import RunContext
from ...core.types import Task, TaskStatus, Message


@dataclass
class SupervisorState:
    """State for supervisor orchestration graph."""
    task: Task
    context: RunContext
    selected_agent: Optional[BaseAgent] = None
    result: Optional[str] = None
    error: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    history: List[Dict[str, Any]] = field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class GroupChatState:
    """State for group chat orchestration graph."""
    message: str
    context: RunContext
    agents: List[BaseAgent]
    current_agent_index: int = 0
    responses: List[Dict[str, str]] = field(default_factory=list)
    conversation_history: List[Message] = field(default_factory=list)
    round: int = 0
    max_rounds: int = 10
    should_continue: bool = True
    sender_id: str = "user"

