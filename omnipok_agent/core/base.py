"""Base agent class with LLM integration."""
import asyncio
import json
import uuid
from abc import ABC
from typing import List, Optional, Dict, Any
from .types import Message, ToolCall, Observation, AgentState, MessageRole
from .context import RunContext
from ..memory.base import Memory
from ..tools.registry import ToolRegistry
from ..llm.omnipok_llm import OmniPokLLM


class BaseAgent(ABC):
    """
    Base agent class with LLM integration.
    
    This is the main base class for all agents. It provides:
    - LLM integration via OmniPokLLM
    - Tool calling support
    - Memory management
    - State management
    - Message handling
    
    Subclasses can extend this to create specialized agents like:
    - TextAgent: For text processing tasks
    - CodeAgent: For code generation and analysis
    - SupportAgent: For customer support
    """
    
    def __init__(
        self,
        agent_id: str,
        name: str,
        llm: Optional[OmniPokLLM] = None,
        memory: Optional[Memory] = None,
        tool_registry: Optional[ToolRegistry] = None,
        system_prompt: Optional[str] = None,
        max_iterations: int = 10
    ):
        """
        Initialize BaseAgent.
        
        Args:
            agent_id: Unique agent identifier
            name: Agent name
            llm: OmniPokLLM instance (recommended)
            memory: Memory backend for state persistence
            tool_registry: Tool registry for agent tools
            system_prompt: System prompt for the agent
            max_iterations: Maximum iterations for tool calling loops
        """
        self.agent_id = agent_id
        self.name = name
        self.memory = memory
        self.tool_registry = tool_registry
        self.system_prompt = system_prompt
        self.state = AgentState()
        self.max_iterations = max_iterations
        
        # Initialize LLM
        if llm:
            self.llm = llm
        else:
            # Auto-detect and create LLM
            self.llm = OmniPokLLM()
    
    async def process(self, message: str, context: RunContext) -> str:
        """
        Process a message and return a response.
        
        This is the main entry point for agent processing. It handles:
        - Message management
        - LLM interaction
        - Tool calling
        - State persistence
        
        Args:
            message: The user message
            context: The run context
            
        Returns:
            The agent's response
        """
        context.start()
        context.increment_step()
        
        try:
            # Add user message
            user_msg = Message(role=MessageRole.USER, content=message)
            self.add_message(user_msg)
            
            # Build conversation history
            messages = self._build_messages()
            
            # Get available tools (only if tool_registry is configured)
            available_tools = []
            if self.tool_registry:
                available_tools = self.get_available_tools(
                    user_permissions=context.metadata.get("permissions", [])
                )
            
            # Call LLM (only pass tools if available)
            response = await self._call_llm(messages, available_tools if available_tools else None)
            
            # Update context with usage if available
            if response.get("usage"):
                usage = response["usage"]
                tokens = usage.get("total_tokens", 0)
                # Estimate cost (this is a placeholder - implement actual cost calculation)
                cost = tokens * 0.000002  # Rough estimate
                context.add_cost(tokens, cost)
            
            # Handle tool calls if any
            final_response = await self._handle_response(response, context)
            
            # Add assistant message
            assistant_msg = Message(
                role=MessageRole.ASSISTANT,
                content=final_response
            )
            self.add_message(assistant_msg)
            
            # Save state
            self.save_state()
            
            return final_response
            
        finally:
            context.end()
    
    async def execute_tool_call(self, tool_call: ToolCall, context: RunContext) -> Observation:
        """
        Execute a tool call.
        
        Args:
            tool_call: The tool call to execute
            context: The run context
            
        Returns:
            The observation from the tool execution
        """
        if not self.tool_registry:
            return Observation(
                tool_call_id=tool_call.id,
                content="No tool registry available",
                is_error=True,
                error_message="Tool registry not configured"
            )
        
        try:
            # Parse arguments if they're a string
            if isinstance(tool_call.arguments, str):
                arguments = json.loads(tool_call.arguments)
            else:
                arguments = tool_call.arguments
            
            # Execute the tool
            result = await self.tool_registry.execute(tool_call.name, arguments)
            
            return Observation(
                tool_call_id=tool_call.id,
                content=result
            )
        except Exception as e:
            return Observation(
                tool_call_id=tool_call.id,
                content=str(e),
                is_error=True,
                error_message=str(e)
            )
    
    def get_state(self) -> AgentState:
        """Get the current agent state."""
        return self.state
    
    def add_message(self, message: Message) -> None:
        """Add a message to the agent's state."""
        self.state.add_message(message)
        if self.memory:
            self.memory.add_message(self.agent_id, message)
    
    def get_available_tools(self, user_permissions: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Get available tools for this agent in OpenAI format."""
        if not self.tool_registry:
            return []
        tools = self.tool_registry.list_tools(user_permissions)
        return [self._convert_tool_to_openai_format(tool.name) for tool in tools]
    
    def _convert_tool_to_openai_format(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        将工具定义转换为OpenAI格式。
        
        Args:
            tool_name: 工具名称
            
        Returns:
            OpenAI格式的工具定义
        """
        tool_schema = self.tool_registry.get_tool_schema(tool_name)
        if not tool_schema:
            return None
        
        # ToolRegistry.get_tool_schema already returns OpenAI-compatible format
        # Just need to wrap it in the standard OpenAI function format
        parameters = tool_schema.get("parameters", {})
        
        return {
            "type": "function",
            "function": {
                "name": tool_schema["name"],
                "description": tool_schema["description"],
                "parameters": parameters
            }
        }
    
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
    
    def _build_messages(self) -> List[Dict[str, Any]]:
        """Build messages for LLM from conversation history."""
        messages = []
        
        # Add system prompt if available
        if self.system_prompt:
            messages.append({
                "role": "system",
                "content": self.system_prompt
            })
        
        # Add conversation history
        for msg in self.state.messages:
            msg_dict = {
                "role": msg.role.value,
                "content": msg.content
            }
            if msg.tool_calls:
                msg_dict["tool_calls"] = [
                    {
                        "id": tc.id,
                        "name": tc.name,
                        "arguments": tc.arguments
                    }
                    for tc in msg.tool_calls
                ]
            if msg.tool_call_id:
                msg_dict["tool_call_id"] = msg.tool_call_id
            messages.append(msg_dict)
        
        return messages
    
    async def _call_llm(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None
    ) -> Dict[str, Any]:
        """Call the LLM with messages and tools."""
        # 使用新的invoke_with_tools方法（同步方法，使用to_thread包装以保持async接口）
        kwargs = {}
        if tool_choice:
            kwargs["tool_choice"] = tool_choice
        response = await asyncio.to_thread(
            self.llm.invoke_with_tools,
            messages=messages,
            tools=tools if tools else None,
            **kwargs
        )
        
        return response
    
    async def _handle_response(
        self,
        response: Dict[str, Any],
        context: RunContext
    ) -> str:
        """Handle LLM response, including tool calls."""
        content = response.get("content", "")
        tool_calls = response.get("tool_calls")
        
        if not tool_calls:
            return content
        
        # Execute tool calls
        observations = []
        for tool_call_data in tool_calls:
            # 解析arguments（可能是字符串或字典）
            arguments = tool_call_data.get("arguments", {})
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except json.JSONDecodeError:
                    arguments = {}
            
            tool_call = ToolCall(
                id=tool_call_data.get("id", str(uuid.uuid4())),
                name=tool_call_data["name"],
                arguments=arguments
            )
            
            observation = await self.execute_tool_call(tool_call, context)
            observations.append(observation)
            
            # Add tool message
            tool_msg = Message(
                role=MessageRole.TOOL,
                content=json.dumps(observation.content) if isinstance(observation.content, dict) else str(observation.content),
                tool_call_id=tool_call.id
            )
            self.add_message(tool_msg)
        
        # If we have observations, call LLM again with the results
        if observations and context.steps_taken < self.max_iterations:
            context.increment_step()
            messages = self._build_messages()
            available_tools = []
            if self.tool_registry:
                available_tools = self.get_available_tools(
                    user_permissions=context.metadata.get("permissions", [])
                )
            next_response = await self._call_llm(messages, available_tools if available_tools else None)
            return await self._handle_response(next_response, context)
        
        return content

