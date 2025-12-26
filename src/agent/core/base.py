"""Base agent interface."""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from ..core.types import Message, ToolCall, Observation, AgentState, MessageRole
from ..core.context import RunContext
from ..core.memory import Memory
from ..core.tool_registry import ToolRegistry


class BaseAgent(ABC):
    """Abstract base class for all agents."""
    
    def __init__(
        self,
        agent_id: str,
        name: str,
        memory: Optional[Memory] = None,
        tool_registry: Optional[ToolRegistry] = None,
        system_prompt: Optional[str] = None
    ):
        self.agent_id = agent_id
        self.name = name
        self.memory = memory
        self.tool_registry = tool_registry
        self.system_prompt = system_prompt
        self.state = AgentState()
    
    @abstractmethod
    async def process(self, message: str, context: RunContext) -> str:
        """
        Process a message and return a response.
        
        Args:
            message: The user message
            context: The run context
            
        Returns:
            The agent's response
        """
        pass
    
    @abstractmethod
    async def execute_tool_call(self, tool_call: ToolCall, context: RunContext) -> Observation:
        """
        Execute a tool call.
        
        Args:
            tool_call: The tool call to execute
            context: The run context
            
        Returns:
            The observation from the tool execution
        """
        pass
    
    def get_state(self) -> AgentState:
        """Get the current agent state."""
        return self.state
    
    def add_message(self, message: Message) -> None:
        """Add a message to the agent's state."""
        self.state.add_message(message)
        if self.memory:
            self.memory.add_message(self.agent_id, message)
    
    def get_available_tools(self, user_permissions: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Get available tools for this agent."""
        if not self.tool_registry:
            return []
        tools = self.tool_registry.list_tools(user_permissions)
        return [self.tool_registry.get_tool_schema(tool.name) for tool in tools]
    
    def load_state(self) -> None:
        """Load state from memory."""
        if self.memory:
            loaded_state = self.memory.load(self.agent_id)
            if loaded_state:
                self.state = loaded_state
    
    def save_state(self) -> None:
        """Save state to memory."""
        if self.memory:
            self.memory.save(self.agent_id, self.state)
    
    def clear_state(self) -> None:
        """Clear the agent's state."""
        self.state = AgentState()
        if self.memory:
            self.memory.clear(self.agent_id)

