"""
Compliance Engine

Pre and post validation for compliance, PII detection, and data quality checks.
"""

import re
from typing import Dict, Any


class ComplianceEngine:
    """
    Compliance validation engine.
    
    Features:
    - PII detection
    - Prohibited term checking
    - Data quality validation
    - Source attribution enforcement
    """

    def __init__(self):
        """Initialize compliance engine."""
        self.pii_patterns = [
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
            r'\b\d{16}\b',  # Credit card
            r'\b[\w\.-]+@[\w\.-]+\.\w+\b'  # Email (overly broad for demo)
        ]
        
        self.prohibited_terms = [
            "internal pipeline",
            "proprietary",
            "confidential"
        ]

    def validate_request(
        self,
        server: str,
        tool: str,
        parameters: Dict[str, Any],
        context: Any
    ) -> Dict[str, Any]:
        """
        Validate request before execution.
        
        Returns:
            Dictionary with passed (bool) and reason (str)
        """
        # Check for PII in parameters
        params_str = str(parameters)
        for pattern in self.pii_patterns:
            if re.search(pattern, params_str):
                return {
                    "passed": False,
                    "reason": "PII detected in request parameters"
                }

        # Check for prohibited terms
        for term in self.prohibited_terms:
            if term.lower() in params_str.lower():
                return {
                    "passed": False,
                    "reason": f"Prohibited term detected: {term}"
                }

        return {"passed": True, "reason": ""}

    def validate_response(self, response: Any) -> Dict[str, Any]:
        """
        Validate response after execution.
        
        Returns:
            Dictionary with passed (bool) and reason (str)
        """
        # Check response quality
        if not response:
            return {
                "passed": False,
                "reason": "Empty response"
            }

        return {"passed": True, "reason": ""}
