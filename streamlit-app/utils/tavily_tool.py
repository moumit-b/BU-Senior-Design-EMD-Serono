import json
import os
from tavily import TavilyClient
from langchain_core.tools import Tool


def tavily_search(tool_input: str) -> str:
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return json.dumps({"error": "Missing TAVILY_API_KEY"})

    try:
        parsed = json.loads(tool_input)
        if isinstance(parsed, dict):
            # Support both "query" and "parameter" keys for backward compatibility
            query = parsed.get("query") or parsed.get("parameter") or ""
        elif isinstance(parsed, str):
            # JSON string input, e.g. `"foo"`
            query = parsed
        else:
            # Unsupported JSON type (e.g. list, number)
            query = ""
    except Exception:
        # Not valid JSON; treat the raw input as the query
        query = tool_input

    # Ensure we have a non-empty search query
    if not query or not str(query).strip():
        return json.dumps({"error": "Missing search query"})
    try:
        client = TavilyClient(api_key=api_key)

        response = client.search(
            query=query,
            search_depth="advanced",
            max_results=5,
            include_answer=True
        )
    except Exception as e:
        error_payload = {
            "error": "Tavily search failed",
            "exception_type": type(e).__name__,
            "message": str(e),
        }
        return json.dumps(error_payload)

    return json.dumps(response, indent=2)


def get_tavily_tool() -> Tool:
    return Tool(
        name="tavily_web_search",
        func=tavily_search,
        description="Search the web for recent information, company news, scientific updates, and competitive intelligence."
    )