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
    Supports Anthropic (standard), Azure OpenAI (Merck), and Ollama (local).
    """
    profile = config_data.get("profile")
    
    if not profile:
        raise ValueError("Invalid configuration: missing profile information")
    
    # Handle different profiles
    if profile.name == "standard":
        provider = config_data.get("llm_provider", "anthropic")
        if provider == "ollama":
            return _get_ollama_llm(config_data, temperature, model_override)
        else:
            return _get_anthropic_llm(config_data, temperature, max_tokens, model_override)
    
    elif profile.name == "merck":
        # For Merck enterprise configuration, check if model is Azure or Bedrock
        model_name = model_override or config_data.get("primary_model", "gpt-4o")
        
        # Determine provider based on model name
        azure_models = config_data.get("azure_models", [])
        bedrock_models = config_data.get("bedrock_models", [])
        
        if model_name in bedrock_models:
            return _get_bedrock_llm(config_data, temperature, max_tokens, model_override)
        else:
            return _get_azure_openai_llm(config_data, temperature, max_tokens, model_override)
    
    else:
        # Default fallback to Anthropic
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


def _get_azure_openai_llm(
    config_data: Dict[str, Any],
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    model_override: Optional[str] = None
):
    """Get Azure OpenAI LLM instance for Merck configuration."""
    try:
        from langchain_openai import AzureChatOpenAI
    except ImportError:
        raise ImportError(
            "langchain-openai is required for Azure OpenAI. "
            "Install with: pip install langchain-openai"
        )

    api_key = config_data.get("api_key")
    if not api_key:
        raise ValueError(
            "Azure OpenAI API key is not set. Please set AZURE_OPENAI_API_KEY in your .env file."
        )

    azure_endpoint = config_data.get("azure_endpoint", "")
    if not azure_endpoint:
        raise ValueError("Azure endpoint is not configured in Merck configuration.")

    model = model_override or config_data.get("primary_model", "gpt-4o")
    temp = temperature if temperature is not None else 0.7
    tokens = max_tokens or 8192

    return AzureChatOpenAI(
        azure_deployment=model,  # In Azure, deployment name = model name
        azure_endpoint=azure_endpoint,
        api_key=api_key,
        api_version="2024-07-18",
        temperature=temp,
        max_tokens=tokens,
    )


def _get_bedrock_llm(
    config_data: Dict[str, Any],
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    model_override: Optional[str] = None
):
    """Get AWS Bedrock Claude LLM instance for Merck configuration."""
    try:
        from langchain_openai import ChatOpenAI
    except ImportError:
        raise ImportError(
            "langchain-openai is required for AWS Bedrock. "
            "Install with: pip install langchain-openai"
        )

    api_key = config_data.get("api_key")
    if not api_key:
        raise ValueError(
            "API key is not set. Please set AZURE_OPENAI_API_KEY in your .env file."
        )

    bedrock_base_url = config_data.get("bedrock_base_url", "")
    if not bedrock_base_url:
        raise ValueError("Bedrock base URL is not configured in Merck configuration.")

    model = model_override or config_data.get("primary_model", "anthropic.claude-3-5-sonnet-20240620-v1:0")
    temp = temperature if temperature is not None else 0.7
    tokens = max_tokens or 8192

    # Format the Bedrock URL with the specific model
    model_url = bedrock_base_url.format(model=model)

    return ChatOpenAI(
        base_url=model_url,
        api_key=api_key,
        model="bedrock",  # Placeholder model name for Bedrock
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
        if profile.name == "standard":
            provider = config_data.get("llm_provider", "anthropic")
            if provider == "ollama":
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
                    
        elif profile.name == "merck":
            api_key = config_data.get("api_key")
            azure_endpoint = config_data.get("azure_endpoint", "")
            bedrock_base_url = config_data.get("bedrock_base_url", "")
            
            if not api_key:
                validation["errors"].append("AZURE_OPENAI_API_KEY not set")
            if not azure_endpoint:
                validation["errors"].append("Azure endpoint not configured")
            if not bedrock_base_url:
                validation["errors"].append("Bedrock base URL not configured")
            
            if api_key and (azure_endpoint or bedrock_base_url):
                validation["ready"] = True
                
                # Determine provider based on current model
                current_model = config_data.get("primary_model", "gpt-4o")
                bedrock_models = config_data.get("bedrock_models", [])
                
                if current_model in bedrock_models:
                    validation["provider"] = "AWS Bedrock"
                    validation["bedrock_base_url"] = bedrock_base_url
                else:
                    validation["provider"] = "Azure OpenAI"
                    validation["azure_endpoint"] = azure_endpoint
                    
                validation["model"] = current_model
                validation["available_models"] = config_data.get("available_models", [])
                validation["azure_models"] = config_data.get("azure_models", [])
                validation["bedrock_models"] = bedrock_models
        else:
            validation["errors"].append(f"Unknown profile: {profile.name}")
            
    except Exception as e:
        validation["errors"].append(f"Validation error: {str(e)}")
    
    return validation
