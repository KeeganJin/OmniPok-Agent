"""Default implementation of BaseAgent."""
import json
import uuid
from typing import List, Optional, Dict, Any
from ..core.base import BaseAgent
from ..core.context import RunContext
from ..core.types import Message, MessageRole, ToolCall, Observation
from ..core.tool_registry import ToolRegistry


class BaseAgentImpl(BaseAgent):
    """Default implementation of BaseAgent with LLM integration."""
    
    def __init__(
        self,
        agent_id: str,
        name: str,
        llm: Optional[OmniPokLLM] = None,
        llm_client: Optional[Any] = None,  # Deprecated: use llm instead
        memory: Optional[Any] = None,
        tool_registry: Optional[ToolRegistry] = None,
        system_prompt: Optional[str] = None,
        max_iterations: int = 10
    ):
        """
        Initialize BaseAgentImpl.
        
        Args:
            agent_id: Unique agent identifier
            name: Agent name
            llm: OmniPokLLM instance (recommended)
            llm_client: Legacy LLM client (deprecated, use llm instead)
            memory: Memory backend
            tool_registry: Tool registry
            system_prompt: System prompt
            max_iterations: Maximum iterations for tool calling
        """
        super().__init__(agent_id, name, memory, tool_registry, system_prompt)
        
        # Support both new llm parameter and legacy llm_client
        if llm:
            self.llm = llm
        elif llm_client:
            # For backward compatibility, wrap legacy client
            if isinstance(llm_client, (OmniPokLLM, LLMProvider)):
                self.llm = llm_client if isinstance(llm_client, OmniPokLLM) else OmniPokLLM(provider="openai")
            else:
                # Try to create OmniPokLLM with auto-detection
                self.llm = OmniPokLLM()
        else:
            # Auto-detect and create LLM
            self.llm = OmniPokLLM()
        
        self.max_iterations = max_iterations
    
    async def process(self, message: str, context: RunContext) -> str:
        """Process a message and return a response."""
        context.start()
        context.increment_step()
        
        try:
            # Add user message
            user_msg = Message(role=MessageRole.USER, content=message)
            self.add_message(user_msg)
            
            # Build conversation history
            messages = self._build_messages()
            
            # Get available tools
            available_tools = self.get_available_tools(
                user_permissions=context.metadata.get("permissions", [])
            )
            
            # Call LLM
            response = await self._call_llm(messages, available_tools)
            
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
        tools: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Call the LLM with messages and tools."""
        # Use the unified LLM interface
        response = await self.llm.chat(messages, tools=tools if tools else None)
        
        # Update context with usage if available
        # This will be done in the process method if context is available
        
        # Convert LLMResponse to dict format
        return {
            "role": response.role,
            "content": response.content,
            "tool_calls": response.tool_calls,
            "finish_reason": response.finish_reason,
            "usage": response.usage
        }
    
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
            tool_call = ToolCall(
                id=tool_call_data.get("id", str(uuid.uuid4())),
                name=tool_call_data["name"],
                arguments=tool_call_data.get("arguments", {})
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
            available_tools = self.get_available_tools(
                user_permissions=context.metadata.get("permissions", [])
            )
            next_response = await self._call_llm(messages, available_tools)
            return await self._handle_response(next_response, context)
        
        return content
    
    async def execute_tool_call(self, tool_call: ToolCall, context: RunContext) -> Observation:
        """Execute a tool call."""
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

