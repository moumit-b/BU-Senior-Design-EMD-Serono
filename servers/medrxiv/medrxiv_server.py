from mcp.server.fastmcp import FastMCP
import asyncio
import medrxiv_web_search as medrxiv

# Create an MCP server
mcp = FastMCP("medrxiv")

@mcp.tool()
async def search_medrxiv_key_words(key_words: str, num_results: int = 10):
    """
    Search articles on medRxiv by keywords.
    
    Args:
        key_words: Keywords to search for.
        num_results: Number of results to return (default 10).
    """
    # Use asyncio.to_thread to run synchronous code in a thread pool
    return await asyncio.to_thread(medrxiv.search_key_words, key_words, num_results)

@mcp.tool()
async def search_medrxiv_advanced(
    term: str = None, 
    title: str = None, 
    author1: str = None, 
    author2: str = None, 
    abstract_title: str = None, 
    text_abstract_title: str = None, 
    section: str = None, 
    start_date: str = None, 
    end_date: str = None, 
    num_results: int = 10
):
    """
    Advanced search for articles on medRxiv with multiple filters.
    
    Args:
        term: General search term.
        title: Title of the article.
        author1: First author name.
        author2: Second author name.
        abstract_title: Abstract or title search.
        text_abstract_title: Text in abstract or title search.
        section: medRxiv section/category.
        start_date: Start date (YYYY-MM-DD).
        end_date: End date (YYYY-MM-DD).
        num_results: Number of results to return.
    """
    return await asyncio.to_thread(
        medrxiv.search_advanced, 
        term, title, author1, author2, abstract_title, 
        text_abstract_title, section, start_date, end_date, num_results
    )

@mcp.tool()
async def get_medrxiv_metadata(doi: str):
    """
    Get detailed metadata for a specific medRxiv article by DOI.
    
    Args:
        doi: Digital Object Identifier (e.g., '10.1101/2023.01.01.23284123').
    """
    return await asyncio.to_thread(medrxiv.doi_get_medrxiv_metadata, doi)

if __name__ == "__main__":
    mcp.run(transport='stdio')
