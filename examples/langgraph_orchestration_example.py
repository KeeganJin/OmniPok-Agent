"""Example usage of LangGraph-based orchestration."""
import asyncio
from omnipok_agent.core import RunContext, Task, TaskStatus, MessageRole
from omnipok_agent.agents import TextAgent, CodeAgent
from omnipok_agent.orchestration.langgraph import LangGraphSupervisor, LangGraphGroupChat
from omnipok_agent.orchestration import SimpleRouter, OrchestrationPolicy


async def supervisor_example():
    """Example: Using LangGraph Supervisor."""
    print("=== LangGraph Supervisor Example ===\n")
    
    # Create agents
    agent1 = TextAgent(
        agent_id="text-agent-1",
        name="Text Agent 1"
    )
    agent2 = CodeAgent(
        agent_id="code-agent-1",
        programming_language="python"
    )
    
    # Create supervisor with LangGraph
    supervisor = LangGraphSupervisor(
        agents=[agent1, agent2],
        router=SimpleRouter(),
        policy=OrchestrationPolicy(),
        max_retries=3
    )
    
    # Create task
    task = Task(
        id="task-1",
        description="Write a Python function to calculate factorial"
    )
    
    # Create context
    context = RunContext(
        tenant_id="test-tenant",
        user_id="test-user",
        budget=10.0,
        max_steps=10
    )
    
    # Assign task
    print(f"Task: {task.description}")
    agent_id = await supervisor.assign_task(task, context)
    
    if agent_id:
        print(f"Task assigned to: {agent_id}")
        print(f"Task status: {task.status}")
        if task.result:
            print(f"Result: {task.result[:100]}...")
    else:
        print("Task assignment failed")
        if task.error:
            print(f"Error: {task.error}")
    
    print()


async def groupchat_example():
    """Example: Using LangGraph GroupChat."""
    print("=== LangGraph GroupChat Example ===\n")
    
    # Create agents
    agent1 = TextAgent(
        agent_id="agent-1",
        name="Agent 1",
        system_prompt="You are a helpful assistant."
    )
    agent2 = TextAgent(
        agent_id="agent-2",
        name="Agent 2",
        system_prompt="You are a creative assistant."
    )
    
    # Create group chat with LangGraph
    groupchat = LangGraphGroupChat(
        agents=[agent1, agent2],
        max_rounds=3
    )
    
    # Create context
    context = RunContext(
        tenant_id="test-tenant",
        user_id="test-user"
    )
    
    # Process message
    message = "What are the benefits of using Python for AI development?"
    print(f"User message: {message}\n")
    
    responses = await groupchat.process_message(
        message=message,
        sender_id="user-1",
        context=context
    )
    
    print("Agent responses:")
    for response in responses:
        print(f"  [{response['agent_name']}]: {response['response'][:100]}...")
    
    print()


async def visualization_example():
    """Example: Visualizing LangGraph workflows."""
    print("=== LangGraph Visualization Example ===\n")
    
    # Create supervisor
    agent1 = TextAgent(agent_id="agent-1", name="Agent 1")
    supervisor = LangGraphSupervisor(agents=[agent1])
    
    print("Supervisor graph structure:")
    print("  - Entry: route")
    print("  - Nodes: route -> validate -> execute")
    print("  - Conditional: validate -> execute (continue) or END (reject)")
    print("  - Conditional: execute -> END (success/fail) or retry -> execute")
    print()
    
    # Try to visualize (requires IPython)
    try:
        supervisor.visualize()
    except Exception as e:
        print(f"Visualization requires IPython: {e}")
        print("Install with: pip install ipython")
    
    print()


if __name__ == "__main__":
    print("LangGraph Orchestration Examples\n")
    print("=" * 50)
    print()
    
    # Run examples
    asyncio.run(supervisor_example())
    asyncio.run(groupchat_example())
    asyncio.run(visualization_example())
    
    print("=" * 50)
    print("Examples completed!")

