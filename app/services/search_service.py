import httpx
import asyncio
from typing import List
from app.models.query import SearchResult
from app.config import Config


class SearchService:
    """Service class for handling search operations with Tavily and Serper APIs."""

    def __init__(self):
        """Initialize the search service with API keys."""
        self.tavily_api_key = Config.TAVILY_API_KEY
        self.serper_api_key = Config.SERPER_API_KEY

    async def search_tavily(self, query: str) -> List[SearchResult]:
        """
        Perform search using Tavily API.
        
        Args:
            query: Search query string
            
        Returns:
            List of SearchResult objects
        """
        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "api_key": self.tavily_api_key,
            "query": query,
            "search_depth": "basic",
            "include_answer": True,
            "include_images": False,
            "include_video": False,
            "max_results": 10
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.tavily.com/search",
                headers=headers,
                json=data
            )
            
            if response.status_code != 200:
                raise Exception(f"Tavily API error: {response.status_code} - {response.text}")
                
            result = response.json()
            results = []
            
            # Add the main answer if available
            if "answer" in result and result["answer"]:
                results.append(SearchResult(
                    title="Summary Answer",
                    url="",
                    content=result["answer"],
                    source="tavily"
                ))
            
            # Add search results
            for item in result.get("results", []):
                results.append(SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    content=item.get("content", ""),
                    source="tavily"
                ))
                
            return results

    async def search_serper(self, query: str) -> List[SearchResult]:
        """
        Perform search using Serper API.
        
        Args:
            query: Search query string
            
        Returns:
            List of SearchResult objects
        """
        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "q": query,
            "gl": "US",  # Geographic location
            "hl": "en",  # Language
            "num": 10    # Number of results
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"https://google.serper.dev/search?key={self.serper_api_key}",
                headers=headers,
                json=data
            )
            
            if response.status_code != 200:
                raise Exception(f"Serper API error: {response.status_code} - {response.text}")
                
            result = response.json()
            results = []
            
            # Add organic search results
            for item in result.get("organic", []):
                results.append(SearchResult(
                    title=item.get("title", ""),
                    url=item.get("link", ""),
                    content=item.get("snippet", ""),
                    source="serper"
                ))
                
            # Add related searches if available
            for item in result.get("relatedSearches", []):
                results.append(SearchResult(
                    title=f"Related: {item.get('query', '')}",
                    url="",
                    content=item.get("query", ""),
                    source="serper"
                ))
                
            return results

    async def search(self, query: str, search_type: str = "tavily") -> List[SearchResult]:
        """
        Main search method that can use either Tavily or Serper.
        
        Args:
            query: Search query string
            search_type: Type of search ("tavily" or "serper")
            
        Returns:
            List of SearchResult objects
        """
        if search_type.lower() == "serper":
            return await self.search_serper(query)
        else:
            return await self.search_tavily(query)

    async def search_streaming(self, query: str, search_type: str = "tavily", callback=None):
        """
        Streaming search that calls callback for each result.
        
        Args:
            query: Search query string
            search_type: Type of search ("tavily" or "serper")
            callback: Callback function to handle each result
        """
        try:
            if search_type.lower() == "serper":
                results = await self.search_serper(query)
            else:
                results = await self.search_tavily(query)
                
            # Simulate real-time streaming by adding random delays
            for i, result in enumerate(results):
                if callback:
                    await callback(result)
                # Random delay to simulate real fetching time
                await asyncio.sleep(0.1 + (i * 0.05))  # Slightly increasing delay
        except Exception as e:
            raise e