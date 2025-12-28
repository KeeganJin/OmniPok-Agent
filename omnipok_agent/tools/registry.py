"""Tool registry for agent tools."""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

try:
    from langchain_core.tools import BaseTool
except ImportError:
    # Fallback if langchain_core is not available
    BaseTool = Any


@dataclass
class ToolDefinition:
    """Definition of a tool."""
    name: str
    description: str
    tool: BaseTool  # LangChain Tool instance
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
        tool: BaseTool,
        name: Optional[str] = None,
        required_permissions: Optional[List[str]] = None
    ) -> None:
        """
        Register a LangChain tool.
        
        Args:
            tool: LangChain Tool instance (from @tool decorator)
            name: Optional custom name (defaults to tool.name)
            required_permissions: Optional list of required permissions
        """
        # Get tool name
        tool_name = name or tool.name
        
        # Extract permissions from metadata if not provided
        if required_permissions is None:
            metadata = getattr(tool, 'metadata', {}) or {}
            required_permissions = metadata.get('required_permissions', [])
        
        tool_def = ToolDefinition(
            name=tool_name,
            description=tool.description,
            tool=tool,
            required_permissions=required_permissions or []
        )
        self._tools[tool_name] = tool_def
    
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
        tool_def = self.get_tool(name)
        if not tool_def:
            raise ValueError(f"Tool '{name}' not found")
        
        # Use LangChain Tool's ainvoke method
        # LangChain Tool's ainvoke handles both sync and async tools
        result = await tool_def.tool.ainvoke(arguments)
        return result
    
    def get_tool_schema(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get the schema for a tool.
        
        Returns a dict with name, description, and parameters in OpenAI format.
        """
        tool_def = self.get_tool(name)
        if not tool_def:
            return None
        
        # Use LangChain Tool's built-in method to convert to OpenAI format
        try:
            # format_tool_to_openai_function returns: {"type": "function", "function": {...}}
            openai_format = tool_def.tool.format_tool_to_openai_function()
            function_def = openai_format.get("function", {})
            
            return {
                "name": function_def.get("name", tool_def.name),
                "description": function_def.get("description", tool_def.description),
                "parameters": function_def.get("parameters", {"type": "object", "properties": {}}),
                "required_permissions": tool_def.required_permissions,
            }
        except (AttributeError, KeyError, TypeError):
            # Fallback: construct basic schema
            return {
                "name": tool_def.name,
                "description": tool_def.description,
                "parameters": {"type": "object", "properties": {}, "required": []},
                "required_permissions": tool_def.required_permissions,
            }


# Global tool registry instance
global_registry = ToolRegistry()

