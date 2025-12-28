"""LangGraph-based group chat implementation."""
from typing import List, Optional
from langgraph.graph import StateGraph, END
from ...core.base import BaseAgent
from ...core.context import RunContext
from ...core.types import Message, MessageRole
from ...memory.base import Memory
from .state import GroupChatState
from .nodes import agent_node


def should_continue_conversation(state: GroupChatState) -> str:
    """
    Conditional edge function: Determine if conversation should continue.
    
    Args:
        state: Current group chat state
        
    Returns:
        "continue" if should continue, "end" otherwise
    """
    # Check max rounds
    if state.round >= state.max_rounds:
        return "end"
    
    # Check if should continue flag is set
    if not state.should_continue:
        return "end"
    
    # Simple heuristic: stop if last few messages are similar
    if len(state.conversation_history) >= 3:
        recent_messages = [
            msg.content for msg in state.conversation_history[-3:]
        ]
        if len(set(recent_messages)) == 1:
            return "end"
    
    return "continue"


def build_groupchat_graph(
    agents: List[BaseAgent],
    max_rounds: int = 10
) -> StateGraph:
    """
    Build the group chat state graph.
    
    Args:
        agents: List of agents participating in the chat
        max_rounds: Maximum number of conversation rounds
        
    Returns:
        Compiled state graph
    """
    # Create graph
    graph = StateGraph(GroupChatState)
    
    # Add agent nodes
    def create_agent_node(agent: BaseAgent):
        """Create an agent node function."""
        async def agent_node_wrapper(state: GroupChatState):
            return await agent_node(state, agent, agent.agent_id)
        return agent_node_wrapper
    
    for agent in agents:
        node_name = f"agent_{agent.agent_id}"
        graph.add_node(node_name, create_agent_node(agent))
    
    # Define edges: sequential flow through agents
    if len(agents) > 0:
        # Start with first agent
        graph.set_entry_point(f"agent_{agents[0].agent_id}")
        
        # Chain agents sequentially
        for i in range(len(agents) - 1):
            current_node = f"agent_{agents[i].agent_id}"
            next_node = f"agent_{agents[i+1].agent_id}"
            graph.add_edge(current_node, next_node)
        
        # Last agent loops back or ends
        last_node = f"agent_{agents[-1].agent_id}"
        graph.add_conditional_edges(
            last_node,
            should_continue_conversation,
            {
                "continue": f"agent_{agents[0].agent_id}",  # Loop back
                "end": END
            }
        )
    
    return graph


class LangGraphGroupChat:
    """
    LangGraph-based group chat for multi-agent collaboration.
    
    This implementation uses LangGraph StateGraph to manage the conversation
    flow, providing better control over the conversation state and flow.
    """
    
    def __init__(
        self,
        agents: List[BaseAgent],
        memory: Optional[Memory] = None,
        max_rounds: int = 10
    ):
        """
        Initialize LangGraph group chat.
        
        Args:
            agents: List of agents participating in the chat
            memory: Optional shared memory
            max_rounds: Maximum number of conversation rounds
        """
        self.agents = {agent.agent_id: agent for agent in agents}
        self.memory = memory
        self.max_rounds = max_rounds
        
        # Build and compile graph
        self.graph = build_groupchat_graph(agents, max_rounds)
        self.compiled = self.graph.compile()
    
    def add_agent(self, agent: BaseAgent) -> None:
        """Add an agent to the group chat."""
        self.agents[agent.agent_id] = agent
        # Note: Graph needs to be rebuilt when agents change
    
    def remove_agent(self, agent_id: str) -> None:
        """Remove an agent from the group chat."""
        if agent_id in self.agents:
            del self.agents[agent_id]
        # Note: Graph needs to be rebuilt when agents change
    
    async def process_message(
        self,
        message: str,
        sender_id: str,
        context: RunContext
    ) -> List[dict]:
        """
        Process a message in the group chat using LangGraph.
        
        Args:
            message: The message content
            sender_id: ID of the sender (user or agent)
            context: The run context
            
        Returns:
            List of responses from agents
        """
        # Create initial user message
        user_msg = Message(
            role=MessageRole.USER,
            content=message,
            name=sender_id
        )
        
        # Create initial state
        initial_state = GroupChatState(
            message=message,
            context=context,
            agents=list(self.agents.values()),
            sender_id=sender_id,
            max_rounds=self.max_rounds,
            conversation_history=[user_msg]
        )
        
        # Execute graph
        try:
            final_state = await self.compiled.ainvoke(initial_state)
            
            # Save to memory if available
            if self.memory:
                for msg in final_state.conversation_history:
                    if msg.role == MessageRole.ASSISTANT:
                        self.memory.add_message(f"groupchat_{msg.name}", msg)
            
            return final_state.responses
        except Exception as e:
            return [{
                "error": str(e),
                "agent_id": "system",
                "response": f"Error processing message: {str(e)}"
            }]
    
    def get_conversation_history(self) -> List[Message]:
        """Get the conversation history (from last execution)."""
        # Note: History is stored in state during execution
        # This would need state tracking for persistent history
        return []
    
    def clear_history(self) -> None:
        """Clear the conversation history."""
        # Note: History is stored in state during execution
        pass
    
    def visualize(self, output_path: Optional[str] = None) -> None:
        """
        Visualize the group chat graph.
        
        Args:
            output_path: Optional path to save the visualization
        """
        try:
            from IPython.display import Image, display
            
            # Generate visualization
            image = self.graph.get_graph().draw_mermaid_png()
            
            if output_path:
                with open(output_path, "wb") as f:
                    f.write(image)
            
            display(Image(image))
        except ImportError:
            print("IPython not available. Install with: pip install ipython")
        except Exception as e:
            print(f"Visualization error: {e}")

