"""Example: Simple agent usage with unified LLM interface."""
import asyncio
from src.agent.core import RunContext, InMemoryMemory, global_registry, OmniPokLLM, HelloAgentsLLM
from src.agent.agents import BaseAgentImpl
from src.agent.tools import http_get

# Register a tool
global_registry.register(
    name="http_get",
    description="Make an HTTP GET request",
    func=http_get
)


async def main():
    """Example usage."""
    # Create LLM instance - framework auto-detects provider
    llm = HelloAgentsLLM()
    
    # Or manually specify provider (optional)
    # llm = HelloAgentsLLM(provider="openai", model="gpt-4")
    # llm = HelloAgentsLLM(provider="modelscope", model="qwen/Qwen2.5-7B-Instruct")
    
    # Create SimpleAgent (using BaseAgentImpl)
    agent = BaseAgentImpl(
        agent_id="agent-1",
        name="AI助手",
        llm=llm,
        system_prompt="你是一个有用的AI助手",
        memory=InMemoryMemory(),
        tool_registry=global_registry
    )
    
    # Create context
    context = RunContext(
        tenant_id="tenant-1",
        user_id="user-1",
        budget=10.0,
        max_steps=10
    )
    
    # Process a message
    response = await agent.process("你好，请介绍一下你自己", context)
    print(f"Agent Response: {response}")
    print(f"Tokens used: {context.tokens_used}")
    print(f"Cost: ${context.cost_incurred:.4f}")


if __name__ == "__main__":
    asyncio.run(main())

