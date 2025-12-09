"""
Common Crawl Integration - Access to 250B+ web pages
"""

from typing import Dict, Any, List, Optional
import httpx
from loguru import logger
import gzip
from io import BytesIO

class CommonCrawlAgent:
    """
    Access Common Crawl dataset for comprehensive web coverage
    """
    
    def __init__(self):
        self.index_url = "https://index.commoncrawl.org"
        self.data_url = "https://data.commoncrawl.org"
        self.current_index = "CC-MAIN-2024-10"  # Update monthly
    
    async def search_index(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search Common Crawl index for URLs matching query
        """
        logger.info(f"🔍 Searching Common Crawl for: {query}")
        
        try:
            # Search CC index
            search_url = f"{self.index_url}/{self.current_index}-index"
            params = {
                "url": f"*.{query}*",
                "output": "json",
                "limit": limit
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(search_url, params=params, timeout=15)
                
                if response.status_code == 200:
                    results = []
                    for line in response.text.strip().split('\n'):
                        if line:
                            import json
                            data = json.loads(line)
                            results.append({
                                "url": data.get("url"),
                                "timestamp": data.get("timestamp"),
                                "filename": data.get("filename"),
                                "offset": data.get("offset"),
                                "length": data.get("length")
                            })
                    
                    logger.info(f"✅ Found {len(results)} results in Common Crawl")
                    return results
        
        except Exception as e:
            logger.error(f"Common Crawl search failed: {e}")
        
        return []
    
    async def fetch_content(self, record: Dict) -> Optional[str]:
        """
        Fetch actual content from Common Crawl
        """
        try:
            # Construct data URL
            url = f"{self.data_url}/{record['filename']}"
            
            # Fetch with range request
            headers = {
                "Range": f"bytes={record['offset']}-{record['offset'] + record['length'] - 1}"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, timeout=20)
                
                if response.status_code == 206:  # Partial content
                    # Decompress WARC record
                    content = gzip.decompress(response.content).decode('utf-8', errors='ignore')
                    
                    # Extract HTML from WARC
                    if "Content-Type: text/html" in content:
                        html_start = content.find("\r\n\r\n")
                        if html_start > 0:
                            html = content[html_start:].strip()
                            return html
        
        except Exception as e:
            logger.error(f"Content fetch failed: {e}")
        
        return None
    
    async def search_and_fetch(self, query: str, limit: int = 5) -> List[Dict]:
        """
        Complete search: find and fetch content
        """
        # Search index
        records = await self.search_index(query, limit)
        
        results = []
        for record in records:
            # Fetch content
            content = await self.fetch_content(record)
            
            if content:
                results.append({
                    "url": record["url"],
                    "content": content[:5000],  # First 5000 chars
                    "timestamp": record["timestamp"]
                })
        
        return results

# Global instance
common_crawl_agent = CommonCrawlAgent()