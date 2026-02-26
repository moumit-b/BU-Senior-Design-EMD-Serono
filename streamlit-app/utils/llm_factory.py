"""
Simplified LLM Factory

Centralized LLM initialization focusing on:
- Anthropic Claude Models (Primary)
- Ollama (Local fallback)
"""

import os
from typing import Optional, Dict, Any


def get_llm_from_config(
    config_data: Dict[str, Any],
    model_override: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None
):
    """
    Get LLM instance based on configuration data.
    Standardized to use Anthropic for all profiles for simplicity.
    """
    profile = config_data.get("profile")
    
    if not profile:
        raise ValueError("Invalid configuration: missing profile information")
    
    # Check for Ollama provider first if in standard profile
    if profile.name == "standard":
        provider = config_data.get("llm_provider", "anthropic")
        if provider == "ollama":
            return _get_ollama_llm(config_data, temperature, model_override)
    
    # All other cases (including Merck) now use Anthropic for simplicity
    return _get_anthropic_llm(config_data, temperature, max_tokens, model_override)


def _get_anthropic_llm(
    config_data: Dict[str, Any],
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    model_override: Optional[str] = None
):
    """Get Anthropic Claude LLM instance."""
    try:
        from langchain_anthropic import ChatAnthropic
    except ImportError:
        raise ImportError(
            "langchain-anthropic is required. "
            "Install with: pip install langchain-anthropic"
        )

    # Use ANTHROPIC_API_KEY for all profiles now
    api_key = config_data.get("anthropic_api_key") or os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY is not set. Please set it in your .env file."
        )

    model = model_override or config_data.get("claude_model", "claude-sonnet-4-5-20250514")
    temp = temperature if temperature is not None else config_data.get("claude_temperature", 0.7)
    tokens = max_tokens or config_data.get("claude_max_tokens", 8192)

    return ChatAnthropic(
        model=model,
        anthropic_api_key=api_key,
        temperature=temp,
        max_tokens=tokens,
    )


def _get_ollama_llm(
    config_data: Dict[str, Any],
    temperature: Optional[float] = None,
    model_override: Optional[str] = None
):
    """Get Ollama LLM instance."""
    try:
        from langchain_ollama import ChatOllama
    except ImportError:
        raise ImportError(
            "langchain-ollama is required for local models."
        )

    model = model_override or config_data.get("ollama_model", "llama3.2")
    base_url = config_data.get("ollama_base_url", "http://localhost:11434")
    temp = temperature if temperature is not None else 0.7

    return ChatOllama(
        model=model,
        base_url=base_url,
        temperature=temp,
    )


def get_llm(
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None
):
    """Legacy function for backward compatibility."""
    from config_manager import config_manager
    config_data = config_manager.load_configuration("standard")
    return _get_anthropic_llm(config_data, temperature, max_tokens)


def validate_llm_setup(config_data: Optional[Dict[str, Any]] = None) -> dict:
    """Validate LLM configuration."""
    if config_data is None:
        import config
        api_key = config.ANTHROPIC_API_KEY or os.getenv("ANTHROPIC_API_KEY")
        return {
            "provider": "anthropic",
            "ready": bool(api_key),
            "model": config.CLAUDE_MODEL if api_key else None,
            "errors": [] if api_key else ["ANTHROPIC_API_KEY not set"]
        }
    
    profile = config_data.get("profile")
    validation = {"profile": profile.name, "ready": False, "errors": []}
    
    try:
        provider = config_data.get("llm_provider", "anthropic")
        if profile.name == "standard" and provider == "ollama":
            validation["ready"] = True
            validation["provider"] = "Ollama (Local)"
            validation["model"] = config_data.get("ollama_model", "llama3.2")
        else:
            api_key = config_data.get("anthropic_api_key") or os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                validation["errors"].append("ANTHROPIC_API_KEY not set")
            else:
                validation["ready"] = True
                validation["provider"] = "Anthropic"
                validation["model"] = config_data.get("claude_model", "claude-sonnet-4-5-20250514")
    except Exception as e:
        validation["errors"].append(f"Validation error: {str(e)}")
    
    return validation
