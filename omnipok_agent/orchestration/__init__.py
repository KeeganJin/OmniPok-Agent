"""Orchestration components for multi-agent systems."""
from .router import Router, SimpleRouter, RoundRobinRouter
from .supervisor import Supervisor
from .policies import (
    BudgetPolicy,
    PermissionPolicy,
    RetryPolicy,
    OrchestrationPolicy,
)
from .groupchat import GroupChat

# LangGraph-based orchestration (optional)
try:
    from .langgraph import (
        LangGraphSupervisor,
        LangGraphGroupChat,
        SupervisorState,
        GroupChatState,
    )
    __all__ = [
        "Router",
        "SimpleRouter",
        "RoundRobinRouter",
        "Supervisor",
        "BudgetPolicy",
        "PermissionPolicy",
        "RetryPolicy",
        "OrchestrationPolicy",
        "GroupChat",
        # LangGraph implementations
        "LangGraphSupervisor",
        "LangGraphGroupChat",
        "SupervisorState",
        "GroupChatState",
    ]
except ImportError:
    # LangGraph not installed, skip LangGraph exports
    __all__ = [
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

