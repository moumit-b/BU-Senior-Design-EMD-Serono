"""
Enhanced LLM Factory

Centralized LLM initialization supporting:
- Anthropic Claude Sonnet 4.5 (standard config)
- Azure OpenAI models (Merck config)
- AWS Bedrock Claude models (Merck config)
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

    Args:
        config_data: Configuration dictionary from ConfigurationManager
        model_override: Override the default model
        temperature: Override default temperature
        max_tokens: Override default max tokens

    Returns:
        LLM instance (ChatAnthropic, AzureChatOpenAI, or ChatOpenAI)

    Raises:
        ValueError: If configuration is invalid or API key is not set
        ImportError: If required packages are not installed
    """
    profile = config_data.get("profile")
    
    if not profile:
        raise ValueError("Invalid configuration: missing profile information")
    
    if profile.name == "standard":
        return _get_anthropic_llm(config_data, temperature, max_tokens, model_override)
    elif profile.name == "merck":
        return _get_merck_llm(config_data, temperature, max_tokens, model_override)
    else:
        raise ValueError(f"Unsupported configuration profile: {profile.name}")


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

    api_key = config_data.get("anthropic_api_key") or os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY is not set. "
            "Set it in your .env file or as an environment variable.\n"
            "  Windows:  set ANTHROPIC_API_KEY=sk-ant-...\n"
            "  Linux/Mac: export ANTHROPIC_API_KEY=sk-ant-..."
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


def _get_merck_llm(
    config_data: Dict[str, Any],
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    model_override: Optional[str] = None
):
    """Get Merck LLM instance (Azure OpenAI or AWS Bedrock)."""
    llm_config_class = config_data.get("llm_config_class")
    
    if not llm_config_class:
        raise ValueError("Merck LLM configuration class not available")
    
    api_key = llm_config_class.get_api_key()
    if not api_key:
        raise ValueError(
            "Merck API key is not set. "
            "Set AZURE_OPENAI_API_KEY or AZURE_API_KEY in your environment variables."
        )
    
    # Determine which model to use
    if model_override:
        model = model_override
    else:
        # Default to GPT-4o for general Q&A tasks
        model = llm_config_class.get_model_for_task("qa")
    
    # Determine if it's an Azure OpenAI or Bedrock model
    if llm_config_class.is_azure_model(model):
        return _get_azure_openai_llm(config_data, model, api_key, temperature, max_tokens)
    elif llm_config_class.is_claude_model(model):
        return _get_bedrock_claude_llm(config_data, model, api_key, temperature, max_tokens)
    else:
        raise ValueError(f"Unsupported model: {model}")


def _get_azure_openai_llm(
    config_data: Dict[str, Any],
    model: str,
    api_key: str,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None
):
    """Get Azure OpenAI LLM instance."""
    try:
        from langchain_openai import AzureChatOpenAI
    except ImportError:
        raise ImportError(
            "langchain-openai is required for Azure OpenAI. "
            "Install with: pip install langchain-openai"
        )
    
    azure_config = config_data.get("azure_openai_config", {})
    
    return AzureChatOpenAI(
        azure_endpoint=azure_config.get("azure_endpoint"),
        azure_deployment=model,  # In Azure, deployment name is often the same as model
        api_version=azure_config.get("api_version", "2024-07-18"),
        api_key=api_key,
        temperature=temperature or 0.7,
        max_tokens=max_tokens or 4096,
    )


def _get_bedrock_claude_llm(
    config_data: Dict[str, Any],
    model: str,
    api_key: str,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None
):
    """Get AWS Bedrock Claude LLM instance via Merck's endpoint."""
    try:
        from langchain_openai import ChatOpenAI
    except ImportError:
        raise ImportError(
            "langchain-openai is required for Bedrock via OpenAI-compatible endpoint. "
            "Install with: pip install langchain-openai"
        )
    
    bedrock_config = config_data.get("aws_bedrock_config", {})
    base_url = bedrock_config.get("base_url", "").format(model=model)
    
    return ChatOpenAI(
        base_url=base_url,
        api_key=api_key,
        model=model,
        temperature=temperature or 0.7,
        max_tokens=max_tokens or 4096,
    )


def get_llm(
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None
):
    """
    Legacy function for backward compatibility.
    Gets Claude LLM instance using standard config.

    Args:
        temperature: Override default temperature
        max_tokens: Override default max tokens

    Returns:
        ChatAnthropic LLM instance

    Raises:
        ValueError: If ANTHROPIC_API_KEY is not set
        ImportError: If required packages are not installed
    """
    # Import here to avoid circular imports
    from config_manager import config_manager
    
    # Load standard configuration
    config_data = config_manager.load_configuration("standard")
    return _get_anthropic_llm(config_data, temperature, max_tokens)


def validate_llm_setup(config_data: Optional[Dict[str, Any]] = None) -> dict:
    """
    Validate LLM configuration for given config data or current loaded config.

    Args:
        config_data: Optional configuration data. If None, uses legacy validation.

    Returns:
        Dictionary with validation results
    """
    if config_data is None:
        # Legacy validation for backward compatibility
        import config
        api_key = config.ANTHROPIC_API_KEY or os.getenv("ANTHROPIC_API_KEY")
        validation = {
            "provider": "anthropic",
            "ready": False,
            "errors": []
        }
        if not api_key:
            validation["errors"].append("ANTHROPIC_API_KEY not set")
        else:
            validation["ready"] = True
            validation["model"] = config.CLAUDE_MODEL
        return validation
    
    # New validation based on configuration data
    profile = config_data.get("profile")
    
    if not profile:
        return {
            "ready": False,
            "errors": ["Invalid configuration: missing profile"]
        }
    
    validation = {
        "profile": profile.name,
        "ready": False,
        "errors": []
    }
    
    try:
        if profile.name == "standard":
            api_key = config_data.get("anthropic_api_key") or os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                validation["errors"].append("ANTHROPIC_API_KEY not set")
            else:
                validation["ready"] = True
                validation["provider"] = "Anthropic"
                validation["model"] = config_data.get("claude_model", "claude-sonnet-4-5-20250514")
                
        elif profile.name == "merck":
            llm_config_class = config_data.get("llm_config_class")
            if not llm_config_class:
                validation["errors"].append("Merck LLM configuration class not available")
            else:
                api_key = llm_config_class.get_api_key()
                if not api_key:
                    validation["errors"].append("Merck API key not set (AZURE_OPENAI_API_KEY or AZURE_API_KEY)")
                else:
                    validation["ready"] = True
                    validation["provider"] = "Azure OpenAI / AWS Bedrock"
                    validation["model"] = llm_config_class.get_model_for_task("qa")
                    validation["organization"] = config_data.get("organization", "Merck R&D")
        
    except Exception as e:
        validation["errors"].append(f"Validation error: {str(e)}")
    
    return validation
