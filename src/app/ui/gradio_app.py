"""Gradio UI for the agent framework."""
import gradio as gr
from typing import Optional, Tuple
from ...agent.core import RunContext
from ...agent.orchestration import Supervisor, SimpleRouter

# Constants
NO_AGENTS_AVAILABLE = "No agents available"

# Global supervisor instance
_supervisor: Optional[Supervisor] = None


def get_supervisor() -> Supervisor:
    """Get or create supervisor instance."""
    global _supervisor
    if _supervisor is None:
        router = SimpleRouter()
        _supervisor = Supervisor(agents=[], router=router)
    return _supervisor


def chat_with_agent(
    message: str,
    history: list,
    agent_id: str
) -> Tuple[list, str]:
    """
    Chat with an agent.
    
    Args:
        message: User message
        history: Conversation history
        agent_id: Agent ID to use
        
    Returns:
        Updated history and empty message
    """
    if not message.strip():
        return history, ""
    
    supervisor = get_supervisor()
    agent = supervisor.get_agent(agent_id)
    
    if not agent:
        history.append((message, "❌ Agent not found."))
        return history, ""
    
    # Create context
    context = RunContext(
        tenant_id="default",
        user_id="user",
        budget=None,
        max_steps=10,
        timeout=60.0
    )
    
    try:
        import asyncio
        response = asyncio.run(agent.process(message, context))
        history.append((message, response))
        
        # Add stats if available
        if context.tokens_used > 0 or context.cost_incurred > 0:
            stats = f"\n\n---\n**Stats:** Steps: {context.steps_taken}, Tokens: {context.tokens_used}, Cost: ${context.cost_incurred:.4f}"
            history.append(("", stats))
    except Exception as e:
        history.append((message, f"❌ Error: {str(e)}"))
    
    return history, ""


def create_gradio_interface():
    """Create Gradio interface."""
    supervisor = get_supervisor()
    agents = supervisor.list_agents()
    
    if not agents:
        agent_choices = [NO_AGENTS_AVAILABLE]
        default_agent = NO_AGENTS_AVAILABLE
    else:
        agent_choices = [f"{agent.name} ({agent.agent_id})" for agent in agents]
        default_agent = agent_choices[0] if agent_choices else NO_AGENTS_AVAILABLE
    
    with gr.Blocks(title="OmniPok Agent Framework") as demo:
        gr.Markdown("# 🤖 OmniPok Agent Framework")
        gr.Markdown("Chat with AI agents powered by the OmniPok framework.")
        
        with gr.Row():
            with gr.Column(scale=1):
                agent_dropdown = gr.Dropdown(
                    choices=agent_choices,
                    value=default_agent,
                    label="Select Agent",
                    interactive=True
                )
                
                gr.Markdown("### Agent Info")
                agent_info = gr.Markdown("Select an agent to see details.")
                
            with gr.Column(scale=2):
                chatbot = gr.Chatbot(
                    label="Conversation",
                    height=500
                )
                
                with gr.Row():
                    msg = gr.Textbox(
                        label="Message",
                        placeholder="Type your message here...",
                        scale=4
                    )
                    submit_btn = gr.Button("Send", scale=1)
        
        def update_agent_info(agent_name_id: str):
            """Update agent info display."""
            if NO_AGENTS_AVAILABLE in agent_name_id:
                return NO_AGENTS_AVAILABLE
            
            # Extract agent ID from selection
            agent_id = agent_name_id.split("(")[1].split(")")[0] if "(" in agent_name_id else ""
            agent = supervisor.get_agent(agent_id)
            
            if not agent:
                return "Agent not found"
            
            tools = agent.get_available_tools()
            info = f"""
### {agent.name}
**ID:** {agent.agent_id}
**Available Tools:** {len(tools)}
"""
            return info
        
        def chat_wrapper(message: str, history: list, agent_selection: str):
            """Wrapper for chat function."""
            if NO_AGENTS_AVAILABLE in agent_selection:
                history.append((message, f"❌ {NO_AGENTS_AVAILABLE}"))
                return history, ""
            
            agent_id = agent_selection.split("(")[1].split(")")[0] if "(" in agent_selection else ""
            return chat_with_agent(message, history, agent_id)
        
        agent_dropdown.change(
            fn=update_agent_info,
            inputs=[agent_dropdown],
            outputs=[agent_info]
        )
        
        msg.submit(
            fn=chat_wrapper,
            inputs=[msg, chatbot, agent_dropdown],
            outputs=[chatbot, msg]
        )
        
        submit_btn.click(
            fn=chat_wrapper,
            inputs=[msg, chatbot, agent_dropdown],
            outputs=[chatbot, msg]
        )
    
    return demo


def launch_gradio(share: bool = False, server_name: str = "0.0.0.0", server_port: int = 7860):
    """Launch Gradio interface."""
    demo = create_gradio_interface()
    demo.launch(share=share, server_name=server_name, server_port=server_port)

