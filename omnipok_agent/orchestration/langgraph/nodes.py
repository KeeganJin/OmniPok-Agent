"""Node implementations for LangGraph orchestration."""
from typing import Dict, Any
from ...orchestration.router import Router
from ...orchestration.policies import OrchestrationPolicy
from .state import SupervisorState, GroupChatState
from ...core.types import Message, MessageRole, TaskStatus


async def route_node(state: SupervisorState) -> SupervisorState:
    """
    Route node: Select an appropriate agent for the task.
    
    Args:
        state: Current supervisor state
        
    Returns:
        Updated state with selected_agent set
    """
    router = state.context.metadata.get("router")
    available_agents = state.context.metadata.get("available_agents", [])
    
    if router and available_agents:
        selected = router.route(state.task, available_agents)
        state.selected_agent = selected
        state.history.append({
            "step": "route",
            "selected_agent": selected.agent_id if selected else None
        })
    else:
        state.status = TaskStatus.FAILED
        state.error = "No router or agents available"
    
    return state


async def validate_node(state: SupervisorState) -> SupervisorState:
    """
    Validate node: Check if task can be assigned to selected agent.
    
    Args:
        state: Current supervisor state
        
    Returns:
        Updated state with validation result
    """
    policy = state.context.metadata.get("policy")
    
    if not state.selected_agent:
        state.status = TaskStatus.FAILED
        state.error = "No agent selected"
        return state
    
    if policy:
        is_valid = policy.validate_task(
            state.task,
            state.selected_agent.agent_id,
            state.context
        )
        if not is_valid:
            state.status = TaskStatus.FAILED
            state.error = "Task validation failed"
            state.history.append({
                "step": "validate",
                "result": "failed",
                "reason": "Policy validation failed"
            })
            return state
    
    state.history.append({
        "step": "validate",
        "result": "passed"
    })
    return state


async def execute_node(state: SupervisorState) -> SupervisorState:
    """
    Execute node: Run the selected agent to process the task.
    
    Args:
        state: Current supervisor state
        
    Returns:
        Updated state with execution result
    """
    if not state.selected_agent:
        state.status = TaskStatus.FAILED
        state.error = "No agent selected"
        return state
    
    try:
        state.status = TaskStatus.IN_PROGRESS
        state.task.status = TaskStatus.IN_PROGRESS
        state.task.assigned_agent = state.selected_agent.agent_id
        
        result = await state.selected_agent.process(
            state.task.description,
            state.context
        )
        
        state.result = result
        state.task.result = result
        state.status = TaskStatus.COMPLETED
        state.task.status = TaskStatus.COMPLETED
        
        state.history.append({
            "step": "execute",
            "result": "success",
            "agent_id": state.selected_agent.agent_id
        })
        
    except Exception as e:
        state.error = str(e)
        state.status = TaskStatus.FAILED
        state.task.status = TaskStatus.FAILED
        state.task.error = str(e)
        
        state.history.append({
            "step": "execute",
            "result": "failed",
            "error": str(e)
        })
    
    return state


async def retry_node(state: SupervisorState) -> SupervisorState:
    """
    Retry node: Retry task execution with backoff.
    
    Args:
        state: Current supervisor state
        
    Returns:
        Updated state ready for retry
    """
    state.retry_count += 1
    state.history.append({
        "step": "retry",
        "attempt": state.retry_count
    })
    
    # Reset error and status for retry
    state.error = None
    state.status = TaskStatus.PENDING
    
    return state


async def agent_node(
    state: GroupChatState,
    agent: Any,
    agent_id: str
) -> GroupChatState:
    """
    Agent node: Process message through an agent.
    
    Args:
        state: Current group chat state
        agent: The agent to process the message
        agent_id: Agent identifier
        
    Returns:
        Updated state with agent response
    """
    # Skip if this is the sender
    if agent_id == state.sender_id:
        return state
    
    # Build conversation context
    conversation_context = _build_conversation_context(state)
    
    try:
        # Process message
        response = await agent.process(conversation_context, state.context)
        
        # Create agent message
        agent_msg = Message(
            role=MessageRole.ASSISTANT,
            content=response,
            name=agent_id
        )
        
        # Add to history
        state.conversation_history.append(agent_msg)
        state.responses.append({
            "agent_id": agent_id,
            "agent_name": agent.name,
            "response": response
        })
        
    except Exception as e:
        # Handle error
        error_msg = Message(
            role=MessageRole.ASSISTANT,
            content=f"Error: {str(e)}",
            name=agent_id
        )
        state.conversation_history.append(error_msg)
        state.responses.append({
            "agent_id": agent_id,
            "agent_name": agent.name,
            "response": f"Error: {str(e)}"
        })
    
    return state


def _build_conversation_context(state: GroupChatState) -> str:
    """Build conversation context from history."""
    context_parts = []
    
    # Add original message
    context_parts.append(f"Original message: {state.message}")
    
    # Add recent conversation history
    for msg in state.conversation_history[-10:]:
        sender = msg.name or msg.role.value
        context_parts.append(f"{sender}: {msg.content}")
    
    return "\n".join(context_parts)

