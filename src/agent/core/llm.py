"""Unified LLM interface for the agent framework."""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import os


@dataclass
class LLMResponse:
    """Response from LLM."""
    content: str
    role: str = "assistant"
    tool_calls: Optional[List[Dict[str, Any]]] = None
    finish_reason: Optional[str] = None
    usage: Optional[Dict[str, int]] = None


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Chat with the LLM.
        
        Args:
            messages: List of messages
            tools: Optional list of tools
            **kwargs: Additional provider-specific arguments
            
        Returns:
            LLMResponse object
        """
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """Get the model name."""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI provider implementation."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4",
        base_url: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize OpenAI provider.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Model name (default: gpt-4)
            base_url: Custom base URL (for OpenAI-compatible APIs)
            **kwargs: Additional OpenAI client arguments
        """
        try:
            from openai import AsyncOpenAI  # type: ignore
        except ImportError as e:
            raise ImportError(
                "OpenAI package not installed. Install it with: pip install openai"
            ) from e
        
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not provided. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        self.model = model
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=base_url,
            **kwargs
        )
    
    async def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> LLMResponse:
        """Chat with OpenAI."""
        # Convert tools to OpenAI format if provided
        openai_tools = None
        if tools:
            openai_tools = [self._tool_to_openai_format(tool) for tool in tools]
        
        # Merge with kwargs
        request_kwargs = {
            "model": self.model,
            "messages": messages,
            **kwargs
        }
        if openai_tools:
            request_kwargs["tools"] = openai_tools
            request_kwargs["tool_choice"] = "auto"
        
        response = await self.client.chat.completions.create(**request_kwargs)
        
        message = response.choices[0].message
        
        # Extract tool calls if present
        tool_calls = None
        if message.tool_calls:
            tool_calls = [
                {
                    "id": tc.id,
                    "name": tc.function.name,
                    "arguments": tc.function.arguments
                }
                for tc in message.tool_calls
            ]
        
        # Extract usage
        usage = None
        if response.usage:
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        
        return LLMResponse(
            content=message.content or "",
            role=message.role or "assistant",
            tool_calls=tool_calls,
            finish_reason=response.choices[0].finish_reason,
            usage=usage
        )
    
    def _tool_to_openai_format(self, tool: Dict[str, Any]) -> Dict[str, Any]:
        """Convert tool to OpenAI format."""
        return {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool.get("description", ""),
                "parameters": {
                    "type": "object",
                    "properties": tool.get("parameters", {}),
                    "required": [
                        name for name, info in tool.get("parameters", {}).items()
                        if info.get("required", False)
                    ]
                }
            }
        }
    
    def get_model_name(self) -> str:
        """Get the model name."""
        return self.model


class ModelScopeProvider(LLMProvider):
    """ModelScope provider implementation (placeholder)."""
    
    def __init__(
        self,
        model: str = "qwen/Qwen2.5-7B-Instruct",
        **kwargs
    ):
        """
        Initialize ModelScope provider.
        
        Args:
            model: Model name
            **kwargs: Additional provider arguments
        """
        self.model = model
        # TODO: Implement ModelScope integration
        raise NotImplementedError("ModelScope provider not yet implemented")
    
    async def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> LLMResponse:
        """Chat with ModelScope (placeholder)."""
        raise NotImplementedError("ModelScope provider not yet implemented")
    
    def get_model_name(self) -> str:
        """Get the model name."""
        return self.model


class OmniPokLLM:
    """Unified LLM interface that supports multiple providers."""
    
    _PROVIDERS = {
        "openai": OpenAIProvider,
        "modelscope": ModelScopeProvider,
    }
    
    def __init__(
        self,
        provider: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize LLM with automatic provider detection or manual specification.
        
        Args:
            provider: Provider name ("openai", "modelscope", etc.)
                     If None, will auto-detect based on available credentials
            **kwargs: Provider-specific arguments
        
        Examples:
            # Auto-detect provider
            llm = OmniPokLLM()
            
            # Manually specify provider
            llm = OmniPokLLM(provider="openai", model="gpt-4")
            llm = OmniPokLLM(provider="modelscope", model="qwen/Qwen2.5-7B-Instruct")
        """
        if provider:
            if provider not in self._PROVIDERS:
                raise ValueError(
                    f"Unknown provider: {provider}. "
                    f"Available providers: {list(self._PROVIDERS.keys())}"
                )
            provider_class = self._PROVIDERS[provider]
        else:
            # Auto-detect provider
            provider_class = self._auto_detect_provider()
        
        self.provider = provider_class(**kwargs)
        self.provider_name = provider or self._detect_provider_name(provider_class)
    
    def _auto_detect_provider(self) -> type[LLMProvider]:
        """Auto-detect provider based on available credentials."""
        # Check for OpenAI API key
        if os.getenv("OPENAI_API_KEY"):
            return OpenAIProvider
        
        # Check for ModelScope credentials
        # TODO: Add ModelScope detection when implemented
        
        # Default to OpenAI if available
        try:
            from openai import AsyncOpenAI  # type: ignore
            return OpenAIProvider
        except ImportError:
            pass
        
        raise ValueError(
            "Could not auto-detect LLM provider. "
            "Please specify provider manually or set required environment variables."
        )
    
    def _detect_provider_name(self, provider_class: type[LLMProvider]) -> str:
        """Detect provider name from class."""
        for name, cls in self._PROVIDERS.items():
            if cls == provider_class:
                return name
        return "unknown"
    
    async def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Chat with the LLM.
        
        Args:
            messages: List of messages
            tools: Optional list of tools
            **kwargs: Additional provider-specific arguments
            
        Returns:
            LLMResponse object
        """
        return await self.provider.chat(messages, tools, **kwargs)
    
    def get_model_name(self) -> str:
        """Get the model name."""
        return self.provider.get_model_name()
    
    def get_provider_name(self) -> str:
        """Get the provider name."""
        return self.provider_name


