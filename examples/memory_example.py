"""Example usage of the new memory system."""
import asyncio
from datetime import datetime
from omnipok_agent.core import RunContext, Message, MessageRole
from omnipok_agent.llm import OmniPokLLM
from omnipok_agent.memory import ShortTermMemory, LongTermMemory, MemoryManager
from omnipok_agent.agents import TextAgent


async def main():
    """Demonstrate memory system usage."""
    print("=== Memory System Example ===\n")
    
    # Example 1: Short-term memory only
    print("1. Short-term Memory Example")
    print("-" * 40)
    short_term = ShortTermMemory(max_messages=5)
    
    agent_id = "test-agent-1"
    for i in range(7):
        message = Message(
            role=MessageRole.USER,
            content=f"Message {i+1}"
        )
        short_term.add_message(agent_id, message)
    
    messages = short_term.get_messages(agent_id)
    print(f"Stored {len(messages)} messages (max 5, showing last 5)")
    for msg in messages:
        print(f"  - {msg.content}")
    print()
    
    # Example 2: Long-term memory (SQLite)
    print("2. Long-term Memory Example")
    print("-" * 40)
    long_term = LongTermMemory(default_importance=50)
    
    agent_id2 = "test-agent-2"
    for i in range(3):
        message = Message(
            role=MessageRole.USER,
            content=f"Important message {i+1}",
            metadata={"important": True}
        )
        long_term.add_message(agent_id2, message, importance=70)
    
    messages = long_term.get_messages(agent_id2)
    print(f"Stored {len(messages)} messages in long-term memory")
    for msg in messages:
        print(f"  - {msg.content}")
    print()
    
    # Example 3: Memory Manager (combines both)
    print("3. Memory Manager Example")
    print("-" * 40)
    manager = MemoryManager(
        auto_archive_threshold=10,
        importance_threshold=30
    )
    
    agent_id3 = "test-agent-3"
    
    # Add some messages
    for i in range(5):
        message = Message(
            role=MessageRole.USER,
            content=f"User message {i+1}"
        )
        manager.add_message(agent_id3, message)
    
    # Add an important message
    important_msg = Message(
        role=MessageRole.SYSTEM,
        content="This is a system message",
        metadata={"important": True}
    )
    manager.add_message(agent_id3, important_msg)
    
    # Retrieve all messages
    all_messages = manager.get_messages(agent_id3)
    print(f"Retrieved {len(all_messages)} messages from manager")
    for msg in all_messages:
        print(f"  - [{msg.role.value}] {msg.content}")
    print()
    
    # Example 4: Using with an agent
    print("4. Using Memory Manager with Agent")
    print("-" * 40)
    
    # Create memory manager
    agent_memory = MemoryManager()
    
    # Create agent with memory manager
    llm = OmniPokLLM()  # Will auto-detect provider
    agent = TextAgent(
        agent_id="memory-agent",
        llm=llm,
        memory=agent_memory,
        system_prompt="You are a helpful assistant with memory."
    )
    
    # Create context
    context = RunContext(
        tenant_id="test-tenant",
        user_id="test-user",
        budget=10.0,
        max_steps=10
    )
    
    print("Agent created with MemoryManager")
    print("Memory will persist across sessions using SQLite")
    print()
    
    # Clean up test data
    print("Cleaning up test data...")
    manager.clear(agent_id3)
    long_term.clear(agent_id2)
    short_term.clear(agent_id)
    print("Done!")


if __name__ == "__main__":
    asyncio.run(main())

