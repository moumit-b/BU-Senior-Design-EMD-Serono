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
