"""Code generation and analysis agent implementation."""
from typing import Optional
from ..core.base import BaseAgent
from ..core.tool_registry import ToolRegistry
from ..core.memory import Memory
from ..core.llm import OmniPokLLM


class CodeAgent(BaseAgent):
    """
    Specialized agent for code-related tasks.
    
    This agent is optimized for:
    - Code generation
    - Code review and analysis
    - Bug fixing
    - Code refactoring
    - Documentation generation
    """
    
    def __init__(
        self,
        agent_id: str,
        llm: Optional[OmniPokLLM] = None,
        memory: Optional[Memory] = None,
        tool_registry: Optional[ToolRegistry] = None,
        programming_language: str = "python"
    ):
        """
        Initialize Code Agent.
        
        Args:
            agent_id: Unique agent identifier
            llm: OmniPokLLM instance (if None, will auto-detect)
            memory: Memory backend
            tool_registry: Tool registry
            programming_language: Primary programming language (default: python)
        """
        system_prompt = f"""You are a specialized code agent with expertise in {programming_language} and software development.

Your capabilities include:
- Writing clean, efficient, and well-documented code
- Reviewing code for bugs, security issues, and best practices
- Refactoring code to improve quality and maintainability
- Generating comprehensive code documentation
- Explaining code functionality and design decisions

Always follow best practices, write production-ready code, and provide clear explanations."""
        
        super().__init__(
            agent_id=agent_id,
            name=f"Code Agent ({programming_language})",
            llm=llm,
            memory=memory,
            tool_registry=tool_registry,
            system_prompt=system_prompt
        )
        self.programming_language = programming_language

