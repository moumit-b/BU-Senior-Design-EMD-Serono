"""
Configuration Manager

Dynamically loads configuration based on user selection.
Supports both standard config.py and Merck-specific config_merck.py.
"""

import importlib
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ConfigurationProfile:
    """Configuration profile metadata"""
    name: str
    display_name: str
    description: str
    organization: str
    module_name: str


class ConfigurationManager:
    """Manages dynamic configuration loading and switching"""
    
    # Available configuration profiles
    PROFILES = {
        "standard": ConfigurationProfile(
            name="standard",
            display_name="Standard Configuration", 
            description="Open-source configuration using Anthropic Claude Sonnet 4.5",
            organization="BU Senior Design",
            module_name="config"
        ),
        "merck": ConfigurationProfile(
            name="merck",
            display_name="Merck Enterprise Configuration",
            description="Enterprise configuration using Azure OpenAI and AWS Bedrock",
            organization="Merck R&D",
            module_name="config_merck"
        )
    }
    
    def __init__(self):
        self._current_profile = None
        self._current_config = None
        
    def load_configuration(self, profile_name: str) -> Dict[str, Any]:
        """
        Load configuration from specified profile.
        
        Args:
            profile_name: Name of the configuration profile ('standard' or 'merck')
            
        Returns:
            Dictionary containing configuration values
            
        Raises:
            ValueError: If profile_name is invalid
            ImportError: If configuration module cannot be loaded
        """
        if profile_name not in self.PROFILES:
            raise ValueError(f"Invalid profile: {profile_name}. Available: {list(self.PROFILES.keys())}")
            
        profile = self.PROFILES[profile_name]
        
        try:
            # Dynamically import the configuration module
            config_module = importlib.import_module(profile.module_name)
            
            if profile_name == "standard":
                # Standard config.py structure
                config_data = {
                    "profile": profile,
                    "llm_provider": getattr(config_module, 'LLM_PROVIDER', 'anthropic'),
                    "claude_model": getattr(config_module, 'CLAUDE_MODEL', 'claude-sonnet-4-5-20250514'),
                    "anthropic_api_key": getattr(config_module, 'ANTHROPIC_API_KEY', ''),
                    "claude_temperature": getattr(config_module, 'CLAUDE_TEMPERATURE', 0.7),
                    "claude_max_tokens": getattr(config_module, 'CLAUDE_MAX_TOKENS', 8192),
                    "ollama_base_url": getattr(config_module, 'OLLAMA_BASE_URL', 'http://localhost:11434'),
                    "ollama_model": getattr(config_module, 'OLLAMA_MODEL', 'llama3.2'),
                    "mcp_servers": getattr(config_module, 'MCP_SERVERS', {}),
                    "feature_flags": getattr(config_module, 'FEATURE_FLAGS', {}),
                }
                
            elif profile_name == "merck":
                # Merck profile uses Azure OpenAI and AWS Bedrock infrastructure
                system_config = getattr(config_module, 'SYSTEM_CONFIG', {})
                merck_llm_config = getattr(config_module, 'MerckLLMConfig', None)
                
                # Combine Azure OpenAI and AWS Bedrock models
                azure_models = merck_llm_config.AZURE_OPENAI_CONFIG["available_models"] if merck_llm_config else []
                bedrock_models = merck_llm_config.AWS_BEDROCK_CONFIG["available_models"] if merck_llm_config else []
                all_models = azure_models + bedrock_models
                
                config_data = {
                    "profile": profile,
                    "organization": system_config.get('organization', 'Merck R&D'),
                    "system_name": system_config.get('system_name', 'Agentic Platform'),
                    "environment": system_config.get('environment', 'production'),
                    "merck_llm_config": merck_llm_config,
                    "azure_endpoint": merck_llm_config.AZURE_OPENAI_CONFIG["azure_endpoint"] if merck_llm_config else "",
                    "bedrock_base_url": merck_llm_config.AWS_BEDROCK_CONFIG["base_url"] if merck_llm_config else "",
                    "primary_model": "gpt-4o",  # Default to Azure OpenAI model
                    "api_key": merck_llm_config.get_api_key() if merck_llm_config else "",
                    "available_models": all_models,
                    "azure_models": azure_models,
                    "bedrock_models": bedrock_models,
                }
            
            self._current_profile = profile_name
            self._current_config = config_data
            
            return config_data
            
        except ImportError as e:
            raise ImportError(f"Failed to load configuration module '{profile.module_name}': {e}")
        except Exception as e:
            raise Exception(f"Error loading configuration for profile '{profile_name}': {e}")
    
    def get_current_config(self) -> Optional[Dict[str, Any]]:
        """Get currently loaded configuration"""
        return self._current_config
    
    def get_current_profile(self) -> Optional[str]:
        """Get current profile name"""
        return self._current_profile
    
    def get_available_profiles(self) -> Dict[str, ConfigurationProfile]:
        """Get all available configuration profiles"""
        return self.PROFILES.copy()
    
    def validate_profile_availability(self, profile_name: str) -> Dict[str, Any]:
        """
        Validate if a configuration profile is available and properly configured.
        
        Returns:
            Dictionary with validation results
        """
        if profile_name not in self.PROFILES:
            return {
                "available": False,
                "error": f"Profile '{profile_name}' not found"
            }
        
        profile = self.PROFILES[profile_name]
        
        try:
            config_data = self.load_configuration(profile_name)
            
            validation = {
                "available": True,
                "profile": profile,
                "config_loaded": True
            }
            
            if profile_name == "standard":
                # Validate Anthropic API key
                api_key = config_data.get("anthropic_api_key")
                validation["api_key_available"] = bool(api_key)
                validation["llm_ready"] = bool(api_key)
                
            elif profile_name == "merck":
                # Validate Merck setup - uses Azure OpenAI API key
                api_key = config_data.get("api_key")
                validation["api_key_available"] = bool(api_key)
                validation["llm_ready"] = bool(api_key)
                validation["azure_endpoint"] = config_data.get("azure_endpoint", "")
                validation["primary_model"] = config_data.get("primary_model", "gpt-4o")
            
            return validation
            
        except Exception as e:
            return {
                "available": False,
                "profile": profile,
                "error": str(e)
            }
    
    def get_llm_info(self, profile_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get LLM information for specified or current profile.
        
        Returns:
            Dictionary with LLM provider, model, and status information
        """
        if profile_name is None:
            profile_name = self._current_profile
            
        if profile_name is None:
            return {"error": "No configuration loaded"}
            
        try:
            config_data = self.load_configuration(profile_name) if profile_name != self._current_profile else self._current_config
            
            if profile_name == "standard":
                provider = config_data.get("llm_provider", "anthropic")
                if provider == "ollama":
                    return {
                        "provider": "Ollama (Local)",
                        "model": config_data.get("ollama_model", "llama3.2"),
                        "base_url": config_data.get("ollama_base_url", "http://localhost:11434"),
                        "api_available": True  # Assume True if configured
                    }
                else:
                    return {
                        "provider": "Anthropic",
                        "model": config_data.get("claude_model", "claude-sonnet-4-5-20250514"),
                        "temperature": config_data.get("claude_temperature", 0.7),
                        "max_tokens": config_data.get("claude_max_tokens", 8192),
                        "api_available": bool(config_data.get("anthropic_api_key"))
                    }
                
            elif profile_name == "merck":
                return {
                    "provider": "Azure OpenAI",
                    "model": config_data.get("primary_model", "gpt-4o"),
                    "azure_endpoint": config_data.get("azure_endpoint", ""),
                    "api_available": bool(config_data.get("api_key")),
                    "available_models": config_data.get("available_models", []),
                    "organization": "Merck R&D"
                }
            
        except Exception as e:
            return {"error": f"Failed to get LLM info: {e}"}


# Global configuration manager instance
config_manager = ConfigurationManager()