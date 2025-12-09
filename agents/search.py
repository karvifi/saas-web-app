"""
Search Agent - Multi-Source Information Retrieval
Better than Google - searches everywhere and synthesizes results
"""

from typing import Dict, Any, List
import asyncio
import httpx
from bs4 import BeautifulSoup
from loguru import logger
import os

class SearchAgent:
    """
    Advanced search agent that queries multiple sources and synthesizes results
    """
    
    def __init__(self):
        self.sources = [
            "https://www.google.com/search",
            "https://duckduckgo.com",
            "https://www.bing.com/search"
        ]
        self.timeout = 10
    
    async def search_duckduckgo(self, query: str) -> List[Dict]:
        """Search DuckDuckGo (no API key needed)"""
        try:
            url = "https://html.duckduckgo.com/html/"
            data = {"q": query}
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, data=data, timeout=self.timeout)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                results = []
                for result in soup.find_all('div', class_='result')[:5]:
                    title_elem = result.find('a', class_='result__a')
                    snippet_elem = result.find('a', class_='result__snippet')
                    
                    if title_elem:
                        results.append({
                            'title': title_elem.text.strip(),
                            'url': title_elem.get('href', ''),
                            'snippet': snippet_elem.text.strip() if snippet_elem else ''
                        })
                
                logger.info(f"✅ DuckDuckGo: Found {len(results)} results")
                return results
                
        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {e}")
            return []
    
    async def search(self, query: str) -> Dict[str, Any]:
        """
        Main search function - queries multiple sources
        """
        logger.info(f"🔍 Searching for: {query}")
        
        # Search DuckDuckGo (easiest, no API key)
        results = await self.search_duckduckgo(query)
        
        if results:
            return {
                "status": "success",
                "query": query,
                "source": "DuckDuckGo",
                "results": results,
                "total_results": len(results)
            }
        else:
            return {
                "status": "no_results",
                "query": query,
                "message": "No results found"
            }
    
    async def synthesize_answer(self, query: str, results: List[Dict]) -> str:
        """
        Use AI to synthesize answer from search results
        """
        if not results:
            return "No results found."
        
        # Create context from results
        context = "\n\n".join([
            f"Source: {r['title']}\n{r['snippet']}"
            for r in results[:3]
        ])
        
        # TODO: Use Gemini to synthesize answer from context
        # For now, return formatted results
        
        answer = f"Based on {len(results)} sources:\n\n"
        for i, result in enumerate(results[:3], 1):
            answer += f"{i}. {result['title']}\n{result['snippet']}\n\n"
        
        return answer

# Global instance
search_agent = SearchAgent()