"""OmniPok Agent Framework."""
from .core import (
    BaseAgent,
    RunContext,
    Message,
    MessageRole,
    ToolCall,
    Observation,
    AgentState,
    Task,
    TaskStatus,
    OmniPokAgentException,
    LLMException,
)
from .memory import (
    Memory,
    InMemoryMemory,
    ShortTermMemory,
    LongTermMemory,
    MemoryManager,
)
from .tools import (
    ToolRegistry,
    ToolDefinition,
    global_registry,
)
from .llm import OmniPokLLM
from .agents import SupportAgent, TextAgent, CodeAgent, ChatAgent, ReActAgent, PlanSolveAgent, ReflectionAgent
# RAGAgent is optionally available
try:
    from .rag import RAGAgent, KnowledgeBase, Document
except ImportError:
    RAGAgent = None
    KnowledgeBase = None
    Document = None
from .orchestration import (
    Router,
    SimpleRouter,
    RoundRobinRouter,
    Supervisor,
    BudgetPolicy,
    PermissionPolicy,
    RetryPolicy,
    OrchestrationPolicy,
    GroupChat,
)

__version__ = "0.1.0"

__all__ = [
    # Core
    "BaseAgent",
    "RunContext",
    "Message",
    "MessageRole",
    "ToolCall",
    "Observation",
    "AgentState",
    "Task",
    "TaskStatus",
    "OmniPokAgentException",
    "LLMException",
    # Memory System
    "Memory",
    "InMemoryMemory",
    "ShortTermMemory",
    "LongTermMemory",
    "MemoryManager",
    # Tools
    "ToolRegistry",
    "ToolDefinition",
    "global_registry",
    # LLM
    "OmniPokLLM",
    # Agents
    "SupportAgent",
    "TextAgent",
    "CodeAgent",
    "ChatAgent",
    "ReActAgent",
    "PlanSolveAgent",
    "ReflectionAgent",
    # RAG (optional)
    "RAGAgent",
    "KnowledgeBase",
    "Document",
    # Orchestration
    "Router",
    "SimpleRouter",
    "RoundRobinRouter",
    "Supervisor",
    "BudgetPolicy",
    "PermissionPolicy",
    "RetryPolicy",
    "OrchestrationPolicy",
    "GroupChat",
]

