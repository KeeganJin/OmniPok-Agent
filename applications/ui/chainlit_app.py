"""Chainlit UI for the agent framework."""
import chainlit as cl
from typing import Optional
from omnipok_agent.core import RunContext
from omnipok_agent.orchestration import Supervisor

# Global supervisor instance (will be set by chainlit_main.py)
_supervisor: Optional[Supervisor] = None


def get_supervisor() -> Supervisor:
    """Get or create supervisor instance."""
    global _supervisor
    if _supervisor is None:
        from omnipok_agent.orchestration import SimpleRouter
        # Initialize supervisor
        router = SimpleRouter()
        _supervisor = Supervisor(agents=[], router=router)
    return _supervisor


def set_supervisor(supervisor: Supervisor) -> None:
    """Set supervisor instance."""
    global _supervisor
    _supervisor = supervisor


@cl.on_chat_start
async def start():
    """Initialize the chat session."""
    supervisor = get_supervisor()
    
    # Get available agents
    agents = supervisor.list_agents()
    
    if not agents:
        await cl.Message(
            content="⚠️ No agents are currently available. Please configure agents first."
        ).send()
        return
    
    # Show available agents
    agent_list = "\n".join([f"- {agent.name} ({agent.agent_id})" for agent in agents])
    await cl.Message(
        content=f"🤖 **Available Agents:**\n{agent_list}\n\nYou can start chatting with any agent!"
    ).send()
    
    # Store supervisor in session
    cl.user_session.set("supervisor", supervisor)
    cl.user_session.set("agents", agents)


@cl.on_message
async def main(message: cl.Message):
    """Handle incoming messages."""
    supervisor = cl.user_session.get("supervisor")
    agents = cl.user_session.get("agents")
    
    if not supervisor or not agents:
        await cl.Message(
            content="❌ Supervisor not initialized. Please refresh the page."
        ).send()
        return
    
    # Use first available agent (or allow user to select)
    agent = agents[0] if agents else None
    
    if not agent:
        await cl.Message(
            content="❌ No agents available."
        ).send()
        return
    
    # Create context
    context = RunContext(
        tenant_id=cl.user_session.get("tenant_id", "default"),
        user_id=cl.user_session.get("user_id", "user"),
        budget=None,
        max_steps=10,
        timeout=60.0
    )
    
    # Show thinking indicator
    msg = cl.Message(content="")
    await msg.send()
    
    try:
        # Process message
        response = await agent.process(message.content, context)
        
        # Update message with response
        msg.content = response
        await msg.update()
        
        # Show metadata if available
        if context.tokens_used > 0 or context.cost_incurred > 0:
            metadata = f"\n\n---\n**Stats:** Steps: {context.steps_taken}, Tokens: {context.tokens_used}, Cost: ${context.cost_incurred:.4f}"
            await cl.Message(content=metadata).send()
            
    except Exception as e:
        await cl.Message(
            content=f"❌ Error: {str(e)}"
        ).send()


@cl.on_stop
async def on_stop():
    """Handle stop event."""
    await cl.Message(content="👋 Session stopped.").send()

