"""Policies for multi-agent orchestration."""
from typing import Dict, List, Optional
from dataclasses import dataclass
from ..core.context import RunContext
from ..core.types import Task


@dataclass
class BudgetPolicy:
    """Budget allocation policy."""
    total_budget: float
    per_agent_budget: Optional[Dict[str, float]] = None
    per_task_budget: Optional[float] = None
    
    def can_allocate(self, agent_id: str, estimated_cost: float) -> bool:
        """Check if budget can be allocated for an agent."""
        if self.per_agent_budget and agent_id in self.per_agent_budget:
            return estimated_cost <= self.per_agent_budget[agent_id]
        if self.per_task_budget:
            return estimated_cost <= self.per_task_budget
        return True  # No specific budget constraint


@dataclass
class PermissionPolicy:
    """Permission-based access control policy."""
    agent_permissions: Dict[str, List[str]]
    required_permissions: Optional[Dict[str, List[str]]] = None
    
    def can_access(self, agent_id: str, resource: str) -> bool:
        """Check if agent has permission to access a resource."""
        agent_perms = self.agent_permissions.get(agent_id, [])
        required_perms = self.required_permissions.get(resource, []) if self.required_permissions else []
        
        if not required_perms:
            return True
        
        return any(perm in agent_perms for perm in required_perms)


@dataclass
class RetryPolicy:
    """Retry policy for failed tasks."""
    max_retries: int = 3
    backoff_factor: float = 1.5
    retryable_errors: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.retryable_errors is None:
            self.retryable_errors = ["timeout", "rate_limit", "temporary_error"]
    
    def should_retry(self, error: str, attempt: int) -> bool:
        """Check if task should be retried."""
        if attempt >= self.max_retries:
            return False
        
        return any(err in error.lower() for err in self.retryable_errors)
    
    def get_backoff_delay(self, attempt: int) -> float:
        """Get backoff delay for retry."""
        return self.backoff_factor ** attempt


class OrchestrationPolicy:
    """Combined orchestration policy."""
    
    def __init__(
        self,
        budget_policy: Optional[BudgetPolicy] = None,
        permission_policy: Optional[PermissionPolicy] = None,
        retry_policy: Optional[RetryPolicy] = None
    ):
        self.budget_policy = budget_policy
        self.permission_policy = permission_policy
        self.retry_policy = retry_policy or RetryPolicy()
    
    def validate_task(self, task: Task, agent_id: str, context: RunContext) -> bool:
        """Validate if task can be assigned to agent."""
        # Check budget
        if self.budget_policy:
            if context.budget:
                if not self.budget_policy.can_allocate(agent_id, context.budget):
                    return False
        
        # Check permissions
        if self.permission_policy:
            if not self.permission_policy.can_access(agent_id, task.id):
                return False
        
        return True

