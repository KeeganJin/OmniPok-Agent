"""Supervisor for managing multiple agents."""
from typing import List, Dict, Optional
from ..core.base import BaseAgent
from ..core.context import RunContext
from ..core.types import Task, TaskStatus
from .router import Router, SimpleRouter
from .policies import OrchestrationPolicy


class Supervisor:
    """Supervisor that manages and coordinates multiple agents."""
    
    def __init__(
        self,
        agents: List[BaseAgent],
        router: Optional[Router] = None,
        policy: Optional[OrchestrationPolicy] = None
    ):
        """
        Initialize supervisor.
        
        Args:
            agents: List of agents to manage
            router: Router for task assignment
            policy: Orchestration policy
        """
        self.agents = {agent.agent_id: agent for agent in agents}
        self.router = router or SimpleRouter()
        self.policy = policy
        self.tasks: Dict[str, Task] = {}
    
    def register_agent(self, agent: BaseAgent) -> None:
        """Register a new agent."""
        self.agents[agent.agent_id] = agent
    
    def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent."""
        if agent_id in self.agents:
            del self.agents[agent_id]
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Get an agent by ID."""
        return self.agents.get(agent_id)
    
    def list_agents(self) -> List[BaseAgent]:
        """List all registered agents."""
        return list(self.agents.values())
    
    async def assign_task(
        self,
        task: Task,
        context: RunContext
    ) -> Optional[str]:
        """
        Assign a task to an appropriate agent.
        
        Args:
            task: The task to assign
            context: The run context
            
        Returns:
            Agent ID if task was assigned, None otherwise
        """
        available_agents = self.list_agents()
        
        if not available_agents:
            task.status = TaskStatus.FAILED
            task.error = "No agents available"
            return None
        
        # Route task to agent
        selected_agent = self.router.route(task, available_agents)
        
        if not selected_agent:
            task.status = TaskStatus.FAILED
            task.error = "No suitable agent found"
            return None
        
        # Validate task assignment
        if self.policy:
            if not self.policy.validate_task(task, selected_agent.agent_id, context):
                task.status = TaskStatus.FAILED
                task.error = "Task validation failed"
                return None
        
        # Update task
        task.assigned_agent = selected_agent.agent_id
        task.status = TaskStatus.IN_PROGRESS
        self.tasks[task.id] = task
        
        # Execute task
        try:
            result = await selected_agent.process(task.description, context)
            task.result = result
            task.status = TaskStatus.COMPLETED
            return selected_agent.agent_id
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            return None
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        return self.tasks.get(task_id)
    
    def list_tasks(self, status: Optional[TaskStatus] = None) -> List[Task]:
        """List all tasks, optionally filtered by status."""
        tasks = list(self.tasks.values())
        if status:
            tasks = [t for t in tasks if t.status == status]
        return tasks

