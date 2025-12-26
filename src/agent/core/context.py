"""Run context for agent execution."""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime
import uuid


@dataclass
class RunContext:
    """Context for a single agent run."""
    tenant_id: str
    user_id: str
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    budget: Optional[float] = None
    max_steps: Optional[int] = None
    timeout: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    # Cost tracking
    tokens_used: int = 0
    cost_incurred: float = 0.0
    
    # Execution tracking
    steps_taken: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    def start(self) -> None:
        """Mark the start of execution."""
        self.start_time = datetime.now()
    
    def end(self) -> None:
        """Mark the end of execution."""
        self.end_time = datetime.now()
    
    def add_cost(self, tokens: int, cost: float) -> None:
        """Add cost to the context."""
        self.tokens_used += tokens
        self.cost_incurred += cost
    
    def increment_step(self) -> None:
        """Increment the step counter."""
        self.steps_taken += 1
    
    def is_budget_exceeded(self) -> bool:
        """Check if budget is exceeded."""
        if self.budget is None:
            return False
        return self.cost_incurred >= self.budget
    
    def is_max_steps_reached(self) -> bool:
        """Check if max steps is reached."""
        if self.max_steps is None:
            return False
        return self.steps_taken >= self.max_steps
    
    def is_timeout(self) -> bool:
        """Check if timeout is reached."""
        if self.timeout is None or self.start_time is None:
            return False
        elapsed = (datetime.now() - self.start_time).total_seconds()
        return elapsed >= self.timeout
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary."""
        return {
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "request_id": self.request_id,
            "budget": self.budget,
            "max_steps": self.max_steps,
            "timeout": self.timeout,
            "tokens_used": self.tokens_used,
            "cost_incurred": self.cost_incurred,
            "steps_taken": self.steps_taken,
            "metadata": self.metadata,
        }

