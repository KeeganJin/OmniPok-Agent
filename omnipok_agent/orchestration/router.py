"""Task router for multi-agent systems."""
from typing import Dict, List, Optional
from abc import ABC, abstractmethod
from ..core.types import Task, TaskStatus
from ..core.base import BaseAgent


class Router(ABC):
    """Abstract router for assigning tasks to agents."""
    
    @abstractmethod
    def route(self, task: Task, available_agents: List[BaseAgent]) -> Optional[BaseAgent]:
        """
        Route a task to an appropriate agent.
        
        Args:
            task: The task to route
            available_agents: List of available agents
            
        Returns:
            The selected agent or None if no suitable agent found
        """
        pass


class SimpleRouter(Router):
    """Simple router that assigns tasks based on agent capabilities."""
    
    def __init__(self, agent_capabilities: Optional[Dict[str, List[str]]] = None):
        """
        Initialize router with agent capabilities.
        
        Args:
            agent_capabilities: Dict mapping agent_id to list of capabilities
        """
        self.agent_capabilities = agent_capabilities or {}
    
    def route(self, task: Task, available_agents: List[BaseAgent]) -> Optional[BaseAgent]:
        """Route task to first available agent or based on capabilities."""
        if not available_agents:
            return None
        
        # If no capabilities defined, use first available agent
        if not self.agent_capabilities:
            return available_agents[0]
        
        # Try to find agent with matching capabilities
        task_keywords = task.description.lower().split()
        
        for agent in available_agents:
            capabilities = self.agent_capabilities.get(agent.agent_id, [])
            for keyword in task_keywords:
                if any(keyword in cap.lower() for cap in capabilities):
                    return agent
        
        # Fallback to first available agent
        return available_agents[0]


class RoundRobinRouter(Router):
    """Round-robin router that distributes tasks evenly."""
    
    def __init__(self):
        self._counter = 0
    
    def route(self, task: Task, available_agents: List[BaseAgent]) -> Optional[BaseAgent]:
        """Route task using round-robin strategy."""
        if not available_agents:
            return None
        
        agent = available_agents[self._counter % len(available_agents)]
        self._counter += 1
        return agent

