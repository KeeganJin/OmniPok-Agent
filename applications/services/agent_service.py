"""Agent service for managing agent instances."""
import os
from typing import Optional
from pathlib import Path

from omnipok_agent.config.agent_config import get_config, AgentServiceConfig
from omnipok_agent.core import (
    RunContext,
)
from omnipok_agent.memory.in_memory import InMemoryMemory
from omnipok_agent.tools.registry import global_registry
from omnipok_agent.llm.omnipok_llm import OmniPokLLM
from omnipok_agent.agents import TextAgent, CodeAgent, SupportAgent
from omnipok_agent.orchestration import Supervisor, SimpleRouter
from omnipok_agent.tools import http_get, http_post, http_put, http_delete


class AgentService:
    """Service for managing agent instances and supervisor."""
    
    _instance: Optional['AgentService'] = None
    _initialized: bool = False
    
    def __new__(cls):
        """Singleton pattern implementation."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the agent service (only once)."""
        if not self._initialized:
            self._supervisor: Optional[Supervisor] = None
            self._config: Optional[AgentServiceConfig] = None
            self._agents: list = []
            type(self)._initialized = True
    
    def initialize(self, config_path: Optional[Path] = None) -> None:
        """
        Initialize the agent service with configuration.
        
        Args:
            config_path: Optional path to config file
        """
        if self._supervisor is not None:
            # Already initialized
            return
        
        # Load configuration
        self._config = get_config(config_path)
        
        # Register default tools
        self._register_default_tools()
        
        # Create agents based on configuration
        self._create_agents()
        
        # Create supervisor
        router = SimpleRouter()
        self._supervisor = Supervisor(agents=self._agents, router=router)
    
    def _register_default_tools(self) -> None:
        """Register default tools in the global registry."""
        # Register LangChain Tool objects directly
        # These are already Tool instances from @tool decorator
        if global_registry.get_tool("http_get") is None:
            global_registry.register(tool=http_get)
        if global_registry.get_tool("http_post") is None:
            global_registry.register(tool=http_post)
        if global_registry.get_tool("http_put") is None:
            global_registry.register(tool=http_put)
        if global_registry.get_tool("http_delete") is None:
            global_registry.register(tool=http_delete)
    
    def _create_llm(self, agent_config) -> OmniPokLLM:
        """
        Create an LLM instance for an agent.
        
        Args:
            agent_config: AgentConfig instance
            
        Returns:
            OmniPokLLM instance
        """
        # Determine provider
        provider = agent_config.llm_provider or self._config.default_llm_provider or "openai"
        
        # Get API key
        api_key_env = agent_config.llm_api_key_env or self._config.default_llm_api_key_env
        api_key = os.getenv(api_key_env)
        
        # Get model
        model = agent_config.llm_model or self._config.default_llm_model or "gpt-4"
        
        if api_key:
            return OmniPokLLM(
                provider=provider,
                api_key=api_key,
                model=model
            )
        else:
            # Fallback to auto-detection
            return OmniPokLLM()
    
    def _create_agents(self) -> None:
        """Create agent instances based on configuration."""
        self._agents = []
        
        for agent_config in self._config.agents:
            if not agent_config.enabled:
                continue
            
            # Create LLM
            llm = self._create_llm(agent_config)
            
            # Create memory
            memory = InMemoryMemory()
            
            # Create agent based on type
            agent = None
            if agent_config.agent_type == "TextAgent":
                agent = TextAgent(
                    agent_id=agent_config.agent_id,
                    name=agent_config.name or "Text Agent",
                    llm=llm,
                    memory=memory,
                    tool_registry=global_registry
                )
            elif agent_config.agent_type == "CodeAgent":
                programming_language = agent_config.programming_language or "python"
                # CodeAgent creates its own name based on programming_language
                agent = CodeAgent(
                    agent_id=agent_config.agent_id,
                    llm=llm,
                    memory=memory,
                    tool_registry=global_registry,
                    programming_language=programming_language
                )
                # Override name if provided in config
                if agent_config.name:
                    agent.name = agent_config.name
            elif agent_config.agent_type == "SupportAgent":
                agent = SupportAgent(
                    agent_id=agent_config.agent_id,
                    name=agent_config.name or "Support Agent",
                    llm=llm,
                    memory=memory,
                    tool_registry=global_registry
                )
            else:
                # Default to TextAgent for unknown types
                print(f"Warning: Unknown agent type '{agent_config.agent_type}', using TextAgent")
                agent = TextAgent(
                    agent_id=agent_config.agent_id,
                    name=agent_config.name or "Text Agent",
                    llm=llm,
                    memory=memory,
                    tool_registry=global_registry
                )
            
            if agent:
                self._agents.append(agent)
    
    def get_supervisor(self) -> Supervisor:
        """
        Get the supervisor instance.
        
        Returns:
            Supervisor instance
            
        Raises:
            RuntimeError: If service is not initialized
        """
        if self._supervisor is None:
            # Auto-initialize if not already done
            self.initialize()
        
        return self._supervisor
    
    def get_agents(self) -> list:
        """
        Get list of agent instances.
        
        Returns:
            List of agent instances
        """
        if not self._agents:
            # Auto-initialize if not already done
            self.initialize()
        
        return self._agents
    
    def reload(self, config_path: Optional[Path] = None) -> None:
        """
        Reload the service with new configuration.
        
        Args:
            config_path: Optional path to config file
        """
        self._supervisor = None
        self._agents = []
        self._config = None
        self.initialize(config_path)
    
    def create_agent(
        self,
        agent_type: str,
        agent_id: str,
        name: Optional[str] = None,
        programming_language: Optional[str] = None,
        llm_provider: Optional[str] = None,
        llm_model: Optional[str] = None,
        llm_api_key_env: Optional[str] = None
    ):
        """
        Dynamically create an agent instance.
        
        Args:
            agent_type: Type of agent ("TextAgent", "CodeAgent", "SupportAgent")
            agent_id: Unique identifier for the agent
            name: Optional name for the agent
            programming_language: Programming language for CodeAgent (default: "python")
            llm_provider: LLM provider (default: from config)
            llm_model: LLM model (default: from config)
            llm_api_key_env: Environment variable name for API key (default: from config)
            
        Returns:
            Created agent instance
            
        Raises:
            ValueError: If agent_type is invalid or agent_id already exists
        """
        # Check if agent_id already exists
        existing_agent = next((a for a in self._agents if a.agent_id == agent_id), None)
        if existing_agent:
            raise ValueError(f"Agent with ID '{agent_id}' already exists")
        
        # Ensure service is initialized
        if self._config is None:
            self.initialize()
        
        # Register default tools if not already done
        self._register_default_tools()
        
        # Create LLM
        if llm_provider or llm_model or llm_api_key_env:
            provider = llm_provider or self._config.default_llm_provider or "openai"
            api_key_env = llm_api_key_env or self._config.default_llm_api_key_env
            api_key = os.getenv(api_key_env)
            model = llm_model or self._config.default_llm_model or "gpt-4"
            
            if api_key:
                llm = OmniPokLLM(provider=provider, api_key=api_key, model=model)
            else:
                llm = OmniPokLLM()
        else:
            # Use default LLM creation logic
            class SimpleAgentConfig:
                def __init__(self):
                    self.llm_provider = None
                    self.llm_model = None
                    self.llm_api_key_env = None
            llm = self._create_llm(SimpleAgentConfig())
        
        # Create memory
        memory = InMemoryMemory()
        
        # Create agent based on type
        agent = None
        if agent_type == "TextAgent":
            agent = TextAgent(
                agent_id=agent_id,
                name=name or "Text Agent",
                llm=llm,
                memory=memory,
                tool_registry=global_registry
            )
        elif agent_type == "CodeAgent":
            programming_language = programming_language or "python"
            agent = CodeAgent(
                agent_id=agent_id,
                llm=llm,
                memory=memory,
                tool_registry=global_registry,
                programming_language=programming_language
            )
            if name:
                agent.name = name
        elif agent_type == "SupportAgent":
            agent = SupportAgent(
                agent_id=agent_id,
                name=name or "Support Agent",
                llm=llm,
                memory=memory,
                tool_registry=global_registry
            )
        else:
            raise ValueError(f"Unknown agent type: {agent_type}. Supported types: TextAgent, CodeAgent, SupportAgent")
        
        # Add agent to list and update supervisor
        if agent:
            self._agents.append(agent)
            # Recreate supervisor with updated agents list
            router = SimpleRouter()
            self._supervisor = Supervisor(agents=self._agents, router=router)
        
        return agent


# Global instance accessor
def get_agent_service() -> AgentService:
    """
    Get the global AgentService instance.
    
    Returns:
        AgentService singleton instance
    """
    return AgentService()

