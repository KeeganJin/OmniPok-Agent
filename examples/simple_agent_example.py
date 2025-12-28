"""Example: Simple agent usage with unified LLM interface."""
import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to Python path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from omnipok_agent.core import RunContext, BaseAgent
from omnipok_agent.memory import InMemoryMemory
from omnipok_agent.tools import global_registry, http_get
from omnipok_agent.llm import OmniPokLLM
from omnipok_agent.agents import TextAgent

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Register a tool
global_registry.register(
    name="http_get",
    description="Make an HTTP GET request",
    func=http_get
)


async def main():
    """Example usage."""
    # Get API key from environment variable
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Warning: OPENAI_API_KEY not found in .env file")
        print("Please create a .env file with your API key:")
        print("OPENAI_API_KEY=your-api-key-here")
        return
    
    # Create LLM instance with API key from .env
    llm = OmniPokLLM(
        provider="openai",
        api_key=api_key,
        model=os.getenv("OPENAI_MODEL", "gpt-4")
    )
    
    # Example 1: Using BaseAgent without tools
    print("=" * 50)
    print("Example 1: BaseAgent (without tools)")
    print("=" * 50)
    agent = BaseAgent(
        agent_id="agent-1",
        name="AI助手",
        llm=llm,
        system_prompt="你是一个有用的AI助手",
        memory=InMemoryMemory()
        # Note: tool_registry is optional - agent works without tools
    )
    
    context = RunContext(
        tenant_id="tenant-1",
        user_id="user-1",
        budget=10.0,
        max_steps=10
    )
    
    response = await agent.process("你好，请介绍一下你自己", context)
    print(f"Agent Response: {response}")
    print(f"Tokens used: {context.tokens_used}")
    print(f"Cost: ${context.cost_incurred:.4f}")
    
    # Example 2: Using TextAgent
    print("\n" + "=" * 50)
    print("Example 2: TextAgent")
    print("=" * 50)
    text_agent = TextAgent(
        agent_id="text-agent-1",
        llm=llm,
        memory=InMemoryMemory(),
        tool_registry=global_registry
    )
    
    context2 = RunContext(
        tenant_id="tenant-1",
        user_id="user-1",
        budget=10.0,
        max_steps=10
    )
    
    response2 = await text_agent.process(
        "请总结一下人工智能的发展历史，用中文回答，不超过200字",
        context2
    )
    print(f"TextAgent Response: {response2}")
    print(f"Tokens used: {context2.tokens_used}")
    print(f"Cost: ${context2.cost_incurred:.4f}")


if __name__ == "__main__":
    asyncio.run(main())

