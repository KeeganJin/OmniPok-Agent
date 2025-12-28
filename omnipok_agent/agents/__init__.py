"""Agent implementations."""
from .support_agent import SupportAgent
from .text_agent import TextAgent
from .code_agent import CodeAgent
from .chat_agent import ChatAgent
from .react_agent import ReActAgent
from .plan_solve_agent import PlanSolveAgent
from .reflection_agent import ReflectionAgent

# RAGAgent is in the rag module, import it separately to avoid circular imports
try:
    from ..rag.rag_agent import RAGAgent
    __all__ = [
        "SupportAgent",
        "TextAgent",
        "CodeAgent",
        "ChatAgent",
        "ReActAgent",
        "PlanSolveAgent",
        "ReflectionAgent",
        "RAGAgent",
    ]
except ImportError:
    # RAG module not available
    __all__ = [
        "SupportAgent",
        "TextAgent",
        "CodeAgent",
        "ChatAgent",
        "ReActAgent",
        "PlanSolveAgent",
        "ReflectionAgent",
    ]

