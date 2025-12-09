"""
Browser Automation Agent
Handles all browser-based tasks with AI control
"""

from playwright.async_api import async_playwright, Browser, Page
from typing import Dict, Any, Optional
from loguru import logger
import os

class BrowserAgent:
    """
    AI-powered browser automation agent
    Can navigate, interact, and extract data from any website
    """
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.headless = os.getenv("HEADLESS", "false").lower() == "true"
    
    async def start(self):
        """Initialize browser"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage'
            ]
        )
        self.page = await self.browser.new_page()
        
        # Set realistic viewport and user agent
        await self.page.set_viewport_size({"width": 1920, "height": 1080})
        await self.page.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        logger.info("✅ Browser agent started")
    
    async def navigate(self, url: str) -> Dict[str, Any]:
        """Navigate to URL"""
        if not self.page:
            await self.start()
        
        try:
            await self.page.goto(url, wait_until="networkidle", timeout=30000)
            logger.info(f"📍 Navigated to: {url}")
            
            return {
                "status": "success",
                "url": self.page.url,
                "title": await self.page.title()
            }
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            return {"status": "error", "message": str(e)}
    
    async def extract_content(self) -> str:
        """Extract text content from current page"""
        if not self.page:
            return ""
        
        content = await self.page.content()
        return content
    
    async def close(self):
        """Close browser"""
        if self.browser:
            await self.browser.close()
            logger.info("🔒 Browser closed")

# Global instance
browser_agent = BrowserAgent()