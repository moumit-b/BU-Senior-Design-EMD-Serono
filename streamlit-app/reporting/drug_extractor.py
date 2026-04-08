"""
Drug/Target Extractor

Analyzes chat conversation history to identify the drug or target
being discussed. Returns None if no drug/target is identified.
"""

import re
from typing import Optional, List, Dict, Any


def extract_drug_from_conversation(
    messages: List[Dict[str, Any]],
    llm=None,
) -> Optional[str]:
    """Extract the primary drug or target from the conversation history.

    Uses the LLM to analyze the conversation and identify the drug/target
    the user is asking about. Returns None if no drug or target is found.

    Args:
        messages: List of chat messages with 'role' and 'content' keys.
        llm: LangChain LLM instance. If None, one will be created.

    Returns:
        The drug/target name as a string, or None if not identified.
    """
    if not messages:
        return None

    # Build a condensed transcript from the conversation
    transcript_parts = []
    for msg in messages:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        # Truncate very long messages to keep the extraction prompt small
        if len(content) > 1500:
            content = content[:1500] + "..."
        transcript_parts.append(f"{role}: {content}")

    transcript = "\n".join(transcript_parts)

    if llm is None:
        try:
            from utils.llm_factory import get_llm
            llm = get_llm(temperature=0)
        except Exception:
            return _fallback_extract(transcript)

    prompt = f"""Analyze the following conversation and identify the PRIMARY drug, compound, or biological target being discussed.

CONVERSATION:
{transcript}

INSTRUCTIONS:
- Return ONLY the name of the drug, compound, or biological target (e.g. "Aspirin", "Pembrolizumab", "PD-L1", "EGFR").
- If there are multiple, return the one that is the main focus of the conversation.
- If the conversation does not discuss any specific drug, compound, or biological target, return exactly: NONE
- Do NOT return any explanation, just the name or NONE."""

    try:
        response = llm.invoke(prompt)
        result = response.content if hasattr(response, "content") else str(response)
        result = result.strip().strip('"').strip("'")

        if result.upper() == "NONE" or len(result) > 100:
            return None
        return result
    except Exception:
        return _fallback_extract(transcript)


def _fallback_extract(text: str) -> Optional[str]:
    """Simple regex fallback when the LLM is unavailable."""
    # Look for common drug name patterns (capitalized words near drug keywords)
    patterns = [
        r"(?:about|discuss|analyze|research|investigate)\s+([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)",
        r"(?:drug|compound|target|molecule|therapy|treatment)\s+(?:called|named|is)?\s*([A-Z][a-zA-Z0-9-]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    return None
