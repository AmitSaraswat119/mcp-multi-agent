"""MCP Server #2: Web Search — web_search, get_answer (via Tavily)."""
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent.parent / ".env")
load_dotenv(Path(__file__).parent.parent.parent / ".env")

from mcp.server.fastmcp import FastMCP
from tavily import TavilyClient

mcp = FastMCP("web_search")


def _get_client() -> TavilyClient:
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise RuntimeError("TAVILY_API_KEY environment variable not set")
    return TavilyClient(api_key=api_key)


@mcp.tool()
def web_search(query: str, max_results: int = 5) -> list[dict]:
    """Search the web for a query and return relevant results.

    Args:
        query: The search query string.
        max_results: Maximum number of results to return (default: 5).

    Returns:
        List of dicts with title, url, content snippet, score.
    """
    client = _get_client()
    response = client.search(
        query=query,
        max_results=max_results,
        include_answer=False,
    )
    results = []
    for r in response.get("results", []):
        results.append({
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "content": r.get("content", ""),
            "score": r.get("score", 0.0),
        })
    return results


@mcp.tool()
def get_answer(query: str) -> str:
    """Get a direct AI-generated answer to a question using web search context.

    Args:
        query: The question to answer.

    Returns:
        A concise answer string synthesized from web search results.
    """
    client = _get_client()
    response = client.search(
        query=query,
        max_results=5,
        include_answer=True,
    )
    answer = response.get("answer", "")
    if not answer:
        # Fall back to first result content
        results = response.get("results", [])
        if results:
            return results[0].get("content", "No answer found.")
        return "No answer found."
    return answer


if __name__ == "__main__":
    mcp.run(transport="stdio")
