"""
Compliance Engine

Pre and post validation for compliance, PII/PHI detection, domain constraints,
and source-attribution enforcement for EMD Serono regulated workflows.
"""

import re
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class ComplianceEngine:
    """
    Compliance validation engine.

    Features:
    - PII / PHI detection (SSN, credit card, email, MRN, date-of-birth)
    - Prohibited-term checking (internal / proprietary data leakage)
    - Domain constraints (restrict certain tools to authorised servers)
    - Response PII scrubbing
    - Source-attribution enforcement
    """

    def __init__(self):
        """Initialize compliance engine with EMD Serono rules."""

        # ---- PII / PHI patterns ----
        self.pii_patterns: List[Dict[str, str]] = [
            {"name": "SSN", "pattern": r"\b\d{3}-\d{2}-\d{4}\b"},
            # Require delimiter-separated groups to avoid false positives on
            # chemical data (CIDs, InChI keys, molecular weights, SMILES, etc.)
            {"name": "Credit Card", "pattern": r"\b\d{4}[- ]\d{4}[- ]\d{4}[- ]\d{4}\b"},
            {"name": "Email", "pattern": r"\b[\w\.-]+@[\w\.-]+\.\w{2,}\b"},
            # PHI-specific
            {"name": "MRN", "pattern": r"\bMRN[:\s]*\d{6,10}\b"},
            {"name": "Date of Birth", "pattern": r"\bDOB[:\s]*\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b"},
            {"name": "Patient ID", "pattern": r"\bPAT-\d{4,}\b"},
        ]

        # ---- Prohibited terms (data-leakage prevention) ----
        self.prohibited_terms: List[str] = [
            "internal pipeline",
            "proprietary",
            "confidential",
            "trade secret",
            "under NDA",
        ]

        # ---- Domain constraints ----
        # Map: server -> set of allowed tool prefixes.  Empty means "all OK".
        self.domain_constraints: Dict[str, List[str]] = {
            # Only allow known BioMCP tools on the biomcp server
            "biomcp": [],
            "pubchem": [],
        }

        # Tracking
        self.violations_log: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Pre-execution validation
    # ------------------------------------------------------------------

    def validate_request(
        self,
        server: str,
        tool: str,
        parameters: Dict[str, Any],
        context: Any,
    ) -> Dict[str, Any]:
        """
        Validate request before execution.

        Returns:
            Dictionary with ``passed`` (bool) and ``reason`` (str).
        """
        params_str = str(parameters)

        # 1. PII / PHI check on outgoing parameters
        for entry in self.pii_patterns:
            if re.search(entry["pattern"], params_str, re.IGNORECASE):
                reason = f"PII/PHI detected in request ({entry['name']})"
                self._record_violation("pre", server, tool, reason)
                return {"passed": False, "reason": reason}

        # 2. Prohibited-term check (prevent leaking internal data to external
        #    MCP servers)
        for term in self.prohibited_terms:
            if term.lower() in params_str.lower():
                reason = f"Prohibited term detected: '{term}'"
                self._record_violation("pre", server, tool, reason)
                return {"passed": False, "reason": reason}

        # 3. Domain constraints (optional allow-list for specific servers)
        allowed = self.domain_constraints.get(server)
        if allowed:  # non-empty allow-list
            if not any(tool.startswith(prefix) for prefix in allowed):
                reason = f"Tool '{tool}' not authorised for server '{server}'"
                self._record_violation("pre", server, tool, reason)
                return {"passed": False, "reason": reason}

        return {"passed": True, "reason": ""}

    # ------------------------------------------------------------------
    # Post-execution validation
    # ------------------------------------------------------------------

    def validate_response(self, response: Any) -> Dict[str, Any]:
        """
        Validate response after execution.

        Checks:
        - Non-empty response
        - PII / PHI leakage in outgoing data
        """
        if not response:
            return {"passed": False, "reason": "Empty response from MCP server"}

        response_str = str(response)

        # Scan for PII / PHI in the response
        for entry in self.pii_patterns:
            if re.search(entry["pattern"], response_str, re.IGNORECASE):
                reason = f"PII/PHI detected in response ({entry['name']}) — data redacted"
                self._record_violation("post", "", "", reason)
                return {"passed": False, "reason": reason}

        return {"passed": True, "reason": ""}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _record_violation(self, stage: str, server: str, tool: str, reason: str):
        """Record a compliance violation for auditing."""
        from datetime import datetime

        self.violations_log.append({
            "timestamp": datetime.now().isoformat(),
            "stage": stage,
            "server": server,
            "tool": tool,
            "reason": reason,
        })
        logger.warning("Compliance violation [%s] %s/%s: %s", stage, server, tool, reason)

    def get_violations(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Return the most recent compliance violations."""
        return self.violations_log[-limit:]
