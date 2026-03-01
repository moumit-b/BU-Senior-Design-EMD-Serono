#!/usr/bin/env python3
"""
Merck-specific configuration file for Agentic Platform.
Standardized on Anthropic Claude infrastructure for simplified deployment.
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Any

# Load environment variables
load_dotenv()

class MerckLLMConfig:
    """Configuration class for Merck's LLM infrastructure"""
    
    # Azure OpenAI Configuration (Primary)
    AZURE_OPENAI_CONFIG = {
        "azure_endpoint": "https://api.nlp.dev.uptimize.merckgroup.com",
        "api_key_env": ["AZURE_OPENAI_API_KEY", "AZURE_API_KEY"],
        "api_version": "2024-07-18",
        "available_models": [
            "gpt-4o",
            "gpt-4-turbo",
            "gpt-35-turbo-16k"
        ]
    }
    
    # AWS Bedrock Configuration (Secondary)
    AWS_BEDROCK_CONFIG = {
        "base_url": "https://api.nlp.dev.uptimize.merckgroup.com/model/{model}/invoke",
        "api_key_env": ["AZURE_OPENAI_API_KEY", "AZURE_API_KEY"],  # Same key for both
        "available_models": [
            "us.anthropic.claude-sonnet-4-20250514-v1:0",
            "anthropic.claude-3-7-sonnet-20250219-v1:0",
            "anthropic.claude-3-5-sonnet-20240620-v1:0"
        ]
    }
    
    # Default model preferences for different tasks
    MODEL_PREFERENCES = {
        "transcription": "gpt-4o",           # Best for understanding context
        "content_analysis": "gpt-4o",        # Comprehensive analysis
        "scoring": "gpt-4o",                 # Consistent scoring
        "qa": "gpt-4o",                      # Question answering
        "fallback": "gpt-35-turbo-16k"       # Faster, cost-effective
    }
    
    # Video processing optimizations for M3 MacBook Pro
    VIDEO_CONFIG = {
        "use_mps": True,                     # Use Metal Performance Shaders
        "max_workers": 8,                    # Optimal for M3 chip
        "chunk_size_seconds": 300,           # 5-minute chunks for transcription
        "audio_sample_rate": 16000,          # Optimal for Whisper
        "video_frame_rate": 1,               # 1 FPS for frame extraction
        "max_video_resolution": (1920, 1080) # Standard HD processing
    }
    
    # Database configuration
    DATABASE_CONFIG = {
        "sqlite_path": "merck_vendor_analysis.db",
        "enable_wal_mode": True,             # Better concurrent access
        "connection_pool_size": 10
    }
    
    @classmethod
    def get_api_key(cls) -> str:
        """Get API key from environment variables"""
        for env_var in cls.AZURE_OPENAI_CONFIG["api_key_env"]:
            api_key = os.getenv(env_var)
            if api_key:
                return api_key
        return None
    
    @classmethod
    def is_api_available(cls) -> bool:
        """Check if API key is available"""
        return cls.get_api_key() is not None
    
    @classmethod
    def get_model_for_task(cls, task: str) -> str:
        """Get recommended model for specific task"""
        return cls.MODEL_PREFERENCES.get(task, cls.MODEL_PREFERENCES["fallback"])
    
    @classmethod
    def is_azure_model(cls, model: str) -> bool:
        """Check if model is Azure OpenAI"""
        return model in cls.AZURE_OPENAI_CONFIG["available_models"]
    
    @classmethod
    def is_claude_model(cls, model: str) -> bool:
        """Check if model is AWS Bedrock Claude"""
        return model in cls.AWS_BEDROCK_CONFIG["available_models"]
# System-wide configuration
SYSTEM_CONFIG = {
    "organization": "Merck R&D",
    "system_name": "Agentic Pharmaceutical Research Platform",
    "version": "1.1.0",
    "environment": "production",
    "logging_level": "INFO",
    "temp_directory": "temp",
    "output_directory": "outputs"
}

# Scoring configuration for pharmaceutical intelligence
SCORING_CONFIG = {
    "scale": {
        "min": 0,
        "max": 5,
        "descriptions": {
            0: "No relevance",
            1: "Minimal relevance",
            2: "Significant gaps", 
            3: "Strong relevance",
            4: "Comprehensive",
            5: "Complete & Actionable"
        }
    },
    "criteria": [
        "scientific_accuracy",
        "research_depth", 
        "competitive_relevance",
        "actionable_insights"
    ]
}

# Export for easy access
def get_config() -> Dict[str, Any]:
    """Get Merck-specific system configuration"""
    return {
        "system": SYSTEM_CONFIG,
        "scoring": SCORING_CONFIG
    }
