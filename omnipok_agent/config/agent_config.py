"""Agent configuration management."""
import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class AgentConfig:
    """Configuration for a single agent."""
    agent_type: str  # "TextAgent", "CodeAgent", "SupportAgent"
    agent_id: str
    name: Optional[str] = None
    llm_provider: Optional[str] = None  # "openai", "anthropic", etc.
    llm_model: Optional[str] = None
    llm_api_key_env: Optional[str] = None  # Environment variable name for API key
    programming_language: Optional[str] = None  # For CodeAgent
    tools: List[str] = field(default_factory=list)  # List of tool names to enable
    enabled: bool = True


@dataclass
class AgentServiceConfig:
    """Configuration for the agent service."""
    agents: List[AgentConfig] = field(default_factory=list)
    default_llm_provider: Optional[str] = None
    default_llm_model: Optional[str] = None
    default_llm_api_key_env: str = "OPENAI_API_KEY"


def load_config_from_env() -> AgentServiceConfig:
    """
    Load agent configuration from environment variables.
    
    Expected format:
    - AGENTS_CONFIG: JSON string with agent configurations
    - Or individual agent configs: AGENT_1_TYPE, AGENT_1_ID, etc.
    
    Returns:
        AgentServiceConfig instance
    """
    config = AgentServiceConfig()
    
    # Try to load from AGENTS_CONFIG JSON
    agents_config_json = os.getenv("AGENTS_CONFIG")
    if agents_config_json:
        try:
            agents_data = json.loads(agents_config_json)
            if isinstance(agents_data, list):
                for agent_data in agents_data:
                    agent_config = AgentConfig(
                        agent_type=agent_data.get("agent_type", "TextAgent"),
                        agent_id=agent_data.get("agent_id", ""),
                        name=agent_data.get("name"),
                        llm_provider=agent_data.get("llm_provider"),
                        llm_model=agent_data.get("llm_model"),
                        llm_api_key_env=agent_data.get("llm_api_key_env"),
                        programming_language=agent_data.get("programming_language"),
                        tools=agent_data.get("tools", []),
                        enabled=agent_data.get("enabled", True)
                    )
                    if agent_config.agent_id:
                        config.agents.append(agent_config)
        except json.JSONDecodeError:
            pass
    
    # If no agents configured, create a default TextAgent
    if not config.agents:
        default_agent = AgentConfig(
            agent_type="TextAgent",
            agent_id="text-agent-1",
            name="Text Agent",
            enabled=True
        )
        config.agents.append(default_agent)
    
    # Set defaults
    config.default_llm_provider = os.getenv("DEFAULT_LLM_PROVIDER", "openai")
    config.default_llm_model = os.getenv("DEFAULT_LLM_MODEL", "gpt-4")
    config.default_llm_api_key_env = os.getenv("DEFAULT_LLM_API_KEY_ENV", "OPENAI_API_KEY")
    
    return config


def load_config_from_file(config_path: Optional[Path] = None) -> AgentServiceConfig:
    """
    Load agent configuration from a JSON file.
    
    Args:
        config_path: Path to config file. If None, looks for config/agents.json
        
    Returns:
        AgentServiceConfig instance
    """
    if config_path is None:
        # Look for config file in project root
        project_root = Path(__file__).parent.parent.parent.parent
        config_path = project_root / "config" / "agents.json"
    
    if not config_path.exists():
        # Fallback to environment variables
        return load_config_from_env()
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        config = AgentServiceConfig()
        
        # Load agent configurations
        agents_data = data.get("agents", [])
        for agent_data in agents_data:
            agent_config = AgentConfig(
                agent_type=agent_data.get("agent_type", "TextAgent"),
                agent_id=agent_data.get("agent_id", ""),
                name=agent_data.get("name"),
                llm_provider=agent_data.get("llm_provider"),
                llm_model=agent_data.get("llm_model"),
                llm_api_key_env=agent_data.get("llm_api_key_env"),
                programming_language=agent_data.get("programming_language"),
                tools=agent_data.get("tools", []),
                enabled=agent_data.get("enabled", True)
            )
            if agent_config.agent_id:
                config.agents.append(agent_config)
        
        # Load defaults
        defaults = data.get("defaults", {})
        config.default_llm_provider = defaults.get("llm_provider", "openai")
        config.default_llm_model = defaults.get("llm_model", "gpt-4")
        config.default_llm_api_key_env = defaults.get("llm_api_key_env", "OPENAI_API_KEY")
        
        # If no agents configured, create a default
        if not config.agents:
            default_agent = AgentConfig(
                agent_type="TextAgent",
                agent_id="text-agent-1",
                name="Text Agent",
                enabled=True
            )
            config.agents.append(default_agent)
        
        return config
        
    except (json.JSONDecodeError, KeyError, IOError) as e:
        # Fallback to environment variables on error
        print(f"Warning: Failed to load config from {config_path}: {e}. Using environment variables.")
        return load_config_from_env()


def get_config(config_path: Optional[Path] = None) -> AgentServiceConfig:
    """
    Get agent configuration, trying file first, then environment variables.
    
    Args:
        config_path: Optional path to config file
        
    Returns:
        AgentServiceConfig instance
    """
    # Try file first
    if config_path or (Path(__file__).parent.parent.parent.parent / "config" / "agents.json").exists():
        return load_config_from_file(config_path)
    
    # Fallback to environment
    return load_config_from_env()

