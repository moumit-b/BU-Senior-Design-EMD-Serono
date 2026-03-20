"""
LLM Factory

Centralized LLM initialization supporting Anthropic Claude Sonnet 4.5.
"""

"""
LLM Factory

Centralized LLM initialization supporting:
- Ollama (local) when LLM_PROVIDER/PROVIDER=ollama
- Anthropic Claude (default) when provider is not ollama
"""

import os
from typing import Optional

import config


def _provider() -> str:
    """
    Determine which LLM provider to use.

    Priority:
      1) LLM_PROVIDER env var
      2) PROVIDER env var
      3) default = "anthropic"
    """
    return (os.getenv("LLM_PROVIDER") or os.getenv("PROVIDER") or "anthropic").lower()


def get_llm(
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None
):
    """
    Get LLM instance based on configuration.

    Args:
        temperature: Override default temperature
        max_tokens: Override default max tokens (used by Anthropic branch)

    Returns:
        LangChain chat model instance (ChatOllama or ChatAnthropic)

    Raises:
        ValueError: If Anthropic is selected but ANTHROPIC_API_KEY is not set
        ImportError: If required provider packages are not installed
    """
    provider = _provider()

    # -------------------------
    # Ollama (local) branch
    # -------------------------
    if provider == "ollama":
        try:
            from langchain_ollama import ChatOllama
        except ImportError:
            raise ImportError(
                "langchain-ollama is required for Ollama. "
                "Install with: pip install langchain-ollama"
            )

        base_url = (
            os.getenv("OLLAMA_BASE_URL")
            or getattr(config, "OLLAMA_BASE_URL", None)
            or "http://localhost:11434"
        )
        model = (
            os.getenv("OLLAMA_MODEL")
            or getattr(config, "OLLAMA_MODEL", None)
            or "llama3.2"
        )

        # ChatOllama doesn't use max_tokens the same way across versions,
        # so we only pass temperature here to stay compatible.
        return ChatOllama(
            model=model,
            base_url=base_url,
            temperature=temperature if temperature is not None else getattr(config, "CLAUDE_TEMPERATURE", 0.7),
        )

    # -------------------------
    # Anthropic branch (default)
    # -------------------------
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
        Dictionary with validation results for the currently selected provider.
    """
    provider = _provider()

    validation = {
        "provider": provider,
        "ready": False,
        "errors": []
    }

    # -------------------------
    # Ollama validation
    # -------------------------
    if provider == "ollama":
        base_url = (
            os.getenv("OLLAMA_BASE_URL")
            or getattr(config, "OLLAMA_BASE_URL", None)
            or "http://localhost:11434"
        )
        model = (
            os.getenv("OLLAMA_MODEL")
            or getattr(config, "OLLAMA_MODEL", None)
            or "llama3.2"
        )

        validation["model"] = model

        # Reachability check for Ollama server
        try:
            import requests
            r = requests.get(f"{base_url}/api/version", timeout=2)
            if r.ok:
                validation["ready"] = True
            else:
                validation["errors"].append(f"Ollama not reachable at {base_url}")
        except Exception:
            validation["errors"].append(f"Ollama not reachable at {base_url}")

        return validation

    # -------------------------
    # Anthropic validation
    # -------------------------
    api_key = config.ANTHROPIC_API_KEY or os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        validation["errors"].append("ANTHROPIC_API_KEY not set")
    else:
        validation["ready"] = True
        validation["model"] = config.CLAUDE_MODEL

    return validation


