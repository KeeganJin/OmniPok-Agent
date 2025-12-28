"""Group chat implementation for multi-agent collaboration."""
from typing import List, Dict, Optional
from ..core.base import BaseAgent
from ..core.context import RunContext
from ..core.types import Message, MessageRole
from ..memory.base import Memory


class GroupChat:
    """Manages group chat between multiple agents."""
    
    def __init__(
        self,
        agents: List[BaseAgent],
        memory: Optional[Memory] = None,
        max_rounds: int = 10
    ):
        """
        Initialize group chat.
        
        Args:
            agents: List of agents participating in the chat
            memory: Optional shared memory
            max_rounds: Maximum number of conversation rounds
        """
        self.agents = {agent.agent_id: agent for agent in agents}
        self.memory = memory
        self.max_rounds = max_rounds
        self.conversation_history: List[Message] = []
        self.current_round = 0
    
    def add_agent(self, agent: BaseAgent) -> None:
        """Add an agent to the group chat."""
        self.agents[agent.agent_id] = agent
    
    def remove_agent(self, agent_id: str) -> None:
        """Remove an agent from the group chat."""
        if agent_id in self.agents:
            del self.agents[agent_id]
    
    async def process_message(
        self,
        message: str,
        sender_id: str,
        context: RunContext
    ) -> List[Dict[str, str]]:
        """
        Process a message in the group chat.
        
        Args:
            message: The message content
            sender_id: ID of the sender (user or agent)
            context: The run context
            
        Returns:
            List of responses from agents
        """
        # Add user message
        user_msg = Message(
            role=MessageRole.USER,
            content=message,
            name=sender_id
        )
        self.conversation_history.append(user_msg)
        
        responses = []
        self.current_round = 0
        
        while self.current_round < self.max_rounds:
            self.current_round += 1
            context.increment_step()
            
            # Each agent processes the conversation
            for agent_id, agent in self.agents.items():
                if agent_id == sender_id:
                    continue  # Skip the sender
                
                # Build context from conversation history
                conversation_context = self._build_conversation_context()
                
                # Agent processes the conversation
                response = await agent.process(conversation_context, context)
                
                # Add agent response
                agent_msg = Message(
                    role=MessageRole.ASSISTANT,
                    content=response,
                    name=agent_id
                )
                self.conversation_history.append(agent_msg)
                
                responses.append({
                    "agent_id": agent_id,
                    "agent_name": agent.name,
                    "response": response
                })
                
                # Save to memory if available
                if self.memory:
                    self.memory.add_message(f"groupchat_{agent_id}", agent_msg)
            
            # Check if conversation should continue
            if self._should_continue():
                break
        
        return responses
    
    def _build_conversation_context(self) -> str:
        """Build conversation context from history."""
        context_parts = []
        for msg in self.conversation_history[-10:]:  # Last 10 messages
            sender = msg.name or msg.role.value
            context_parts.append(f"{sender}: {msg.content}")
        return "\n".join(context_parts)
    
    def _should_continue(self) -> bool:
        """Determine if conversation should continue."""
        # Simple heuristic: stop if last few messages are similar
        if len(self.conversation_history) < 2:
            return True
        
        # Check if agents are repeating themselves
        recent_messages = [msg.content for msg in self.conversation_history[-3:]]
        if len(set(recent_messages)) == 1:
            return False
        
        return True
    
    def get_conversation_history(self) -> List[Message]:
        """Get the conversation history."""
        return self.conversation_history.copy()
    
    def clear_history(self) -> None:
        """Clear the conversation history."""
        self.conversation_history = []
        self.current_round = 0

