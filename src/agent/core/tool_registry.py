"""Tool registry for agent tools."""
from abc import ABC, abstractmethod
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass
import inspect


@dataclass
class ToolDefinition:
    """Definition of a tool."""
    name: str
    description: str
    func: Callable
    parameters: Dict[str, Any]
    required_permissions: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.required_permissions is None:
            self.required_permissions = []


class ToolRegistry:
    """Registry for managing agent tools."""
    
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
    
    def register(
        self,
        name: str,
        description: str,
        func: Callable,
        required_permissions: Optional[List[str]] = None
    ) -> None:
        """Register a tool."""
        # Extract function signature
        sig = inspect.signature(func)
        parameters = {}
        for param_name, param in sig.parameters.items():
            param_info = {
                "type": str(param.annotation) if param.annotation != inspect.Parameter.empty else "string",
                "required": param.default == inspect.Parameter.empty,
            }
            if param.default != inspect.Parameter.empty:
                param_info["default"] = param.default
            parameters[param_name] = param_info
        
        tool_def = ToolDefinition(
            name=name,
            description=description,
            func=func,
            parameters=parameters,
            required_permissions=required_permissions or []
        )
        self._tools[name] = tool_def
    
    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """Get a tool by name."""
        return self._tools.get(name)
    
    def list_tools(self, user_permissions: Optional[List[str]] = None) -> List[ToolDefinition]:
        """List all available tools, optionally filtered by permissions."""
        if user_permissions is None:
            return list(self._tools.values())
        
        # Filter tools based on permissions
        available_tools = []
        for tool in self._tools.values():
            if not tool.required_permissions or any(
                perm in user_permissions for perm in tool.required_permissions
            ):
                available_tools.append(tool)
        
        return available_tools
    
    async def execute(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a tool (supports both sync and async tools)."""
        tool = self.get_tool(name)
        if not tool:
            raise ValueError(f"Tool '{name}' not found")
        
        import inspect
        if inspect.iscoroutinefunction(tool.func):
            return await tool.func(**arguments)
        return tool.func(**arguments)
    
    def get_tool_schema(self, name: str) -> Optional[Dict[str, Any]]:
        """Get the schema for a tool."""
        tool = self.get_tool(name)
        if not tool:
            return None
        
        return {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters,
            "required_permissions": tool.required_permissions,
        }


# Global tool registry instance
global_registry = ToolRegistry()

