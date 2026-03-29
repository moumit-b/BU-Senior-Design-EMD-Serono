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
        query = parsed.get("query", "")
    except Exception:
        query = tool_input

    client = TavilyClient(api_key=api_key)

    response = client.search(
        query=query,
        search_depth="advanced",
        max_results=5,
        include_answer=True
    )

    return json.dumps(response, indent=2)


def get_tavily_tool() -> Tool:
    return Tool(
        name="tavily_web_search",
        func=tavily_search,
        description="Search the web for recent information, company news, scientific updates, and competitive intelligence."
    )