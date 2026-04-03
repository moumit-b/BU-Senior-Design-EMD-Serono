"""
Chat-based Report Generator

Generates structured reports from chat conversation history using the
EMD Biopharma R&D report format. The LLM is instructed to follow the
format strictly and fill in sections based on available knowledge.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path


# ---------------------------------------------------------------------------
# EMD report format template (loaded once)
# ---------------------------------------------------------------------------

_EMD_FORMAT_CACHE: Optional[str] = None


def _load_emd_format() -> str:
    """Load the EMD report format markdown from docs/."""
    global _EMD_FORMAT_CACHE
    if _EMD_FORMAT_CACHE is not None:
        return _EMD_FORMAT_CACHE

    fmt_path = Path(__file__).resolve().parent.parent / "docs" / "EMD_report_format.md"
    if fmt_path.exists():
        _EMD_FORMAT_CACHE = fmt_path.read_text(encoding="utf-8")
    else:
        _EMD_FORMAT_CACHE = ""
    return _EMD_FORMAT_CACHE


def _get_report_llm(config_data: Optional[Dict[str, Any]] = None):
    """Create an LLM configured for report generation.

    Uses higher max_tokens (16384) and lower temperature (0.3) than the
    chat agent to produce thorough, structured, factual reports.
    """
    if config_data:
        from utils.llm_factory import get_llm_from_config
        return get_llm_from_config(config_data, temperature=0.3, max_tokens=16384)
    else:
        from utils.llm_factory import get_llm
        return get_llm(temperature=0.3, max_tokens=16384)


def generate_report_from_chat(
    messages: List[Dict[str, Any]],
    drug_name: str,
    report_type: str = "competitive_intelligence",
    config_data: Optional[Dict[str, Any]] = None,
) -> str:
    """Generate a full report from chat conversation context.

    Args:
        messages: Chat history (list of dicts with 'role' and 'content').
        drug_name: The identified drug or target.
        report_type: Which report template to use.
        config_data: Configuration data for LLM creation. Respects the
            user's selected provider (standard/merck/ollama).

    Returns:
        The complete report as a Markdown string.
    """
    llm = _get_report_llm(config_data)

    emd_format = _load_emd_format()

    # Build a condensed conversation transcript for context
    transcript = _build_transcript(messages)

    if report_type == "competitive_intelligence":
        return _generate_ci_report(llm, drug_name, transcript, emd_format)

    # Fallback — shouldn't happen with the current UI
    return f"# Report\n\nReport type '{report_type}' is not yet implemented."


def _build_transcript(messages: List[Dict[str, Any]], max_chars: int = 12000) -> str:
    """Condense messages into a transcript string for the LLM prompt."""
    parts = []
    total = 0
    for msg in messages:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        line = f"{role}: {content}"
        if total + len(line) > max_chars:
            remaining = max_chars - total
            if remaining > 100:
                parts.append(line[:remaining] + "...")
            break
        parts.append(line)
        total += len(line)
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Competitive Intelligence Report
# ---------------------------------------------------------------------------


def _generate_ci_report(
    llm, drug_name: str, transcript: str, emd_format: str
) -> str:
    """Generate a Competitive Intelligence report following the EMD format."""

    report_date = datetime.now().strftime("%Y-%m-%d")

    prompt = f"""You are a senior pharmaceutical intelligence analyst generating a **Competitive Intelligence Report** for the drug / target: **{drug_name}**.

## Report Structure Reference
The report MUST follow the structure defined below. Use the exact section numbering, headings, and table formats. Fill in every field you can based on your knowledge. If you lack data for a field, write "Data not available" rather than omitting the section.

<report_format>
{emd_format}
</report_format>

## Conversation Context
The user has been researching this subject. Here is their conversation for additional context on what they care about:

<conversation>
{transcript}
</conversation>

## Instructions
1. Generate a Competitive Intelligence Report for **{drug_name}** following the EMD report structure above.
2. **CORE SECTIONS** — provide thorough, detailed content with fully populated tables:
   - Section 1 (Executive Summary & 6R Framework)
   - Section 2 (General Target and Biomarker Information)
   - Section 9 (Competitive Landscape) — this is the PRIMARY section, be exhaustive
   - Section 8 (Regulatory and Commercial Overview)
   - Section 11 (Target Landscape and Development Trends)
   - Section 17 (Risks, Gaps, and Recommended Next Steps)
3. **NON-CORE SECTIONS** (3, 4, 5, 6, 7, 10, 12, 13, 14, 15, 16, 18) — include the section heading and a brief summary (2-3 sentences) or write "Not applicable to competitive intelligence scope." Do NOT generate full tables or extensive detail for these sections.
4. Use the EXACT markdown table formats from the template for core sections.
5. Fill in the header fields:
   - **Report Date:** {report_date}
   - **Prepared By:** AI Research Intelligence System
6. Be factual. Cite specific drugs, companies, trial NCT numbers, and mechanisms where possible.
7. Output ONLY the markdown report — no preamble, no commentary outside the report.
8. Allocate approximately 60% of the report content to the core sections listed in instruction 2. Keep the total report under 12,000 words.

Generate the report now:"""

    try:
        response = llm.invoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)
        return content.strip()
    except Exception as e:
        return (
            f"# Competitive Intelligence Report — {drug_name}\n\n"
            f"**Error:** Report generation failed: {e}\n\n"
            f"Please check your LLM configuration and try again."
        )
