"""
LLM Factory

Centralized LLM initialization supporting Anthropic Claude Sonnet 4.5.
"""

import os
import config
from typing import Optional


def get_llm(
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None
):
    """
    Get Claude LLM instance based on configuration.

    Args:
        temperature: Override default temperature
        max_tokens: Override default max tokens

    Returns:
        ChatAnthropic LLM instance

    Raises:
        ValueError: If ANTHROPIC_API_KEY is not set
        ImportError: If required packages are not installed
    """
    try:
        from langchain_anthropic import ChatAnthropic
    except ImportError:
        raise ImportError(
            "langchain-anthropic is required. "
            "Install with: pip install langchain-anthropic"
        )

    api_key = config.ANTHROPIC_API_KEY or os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY is not set. "
            "Set it in your .env file or as an environment variable.\n"
            "  Windows:  set ANTHROPIC_API_KEY=sk-ant-...\n"
            "  Linux/Mac: export ANTHROPIC_API_KEY=sk-ant-..."
        )

    return ChatAnthropic(
        model=config.CLAUDE_MODEL,
        anthropic_api_key=api_key,
        temperature=temperature if temperature is not None else config.CLAUDE_TEMPERATURE,
        max_tokens=max_tokens or config.CLAUDE_MAX_TOKENS,
    )


def validate_llm_setup() -> dict:
    """
    Validate LLM configuration.

    Returns:
        Dictionary with validation results
    """
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
