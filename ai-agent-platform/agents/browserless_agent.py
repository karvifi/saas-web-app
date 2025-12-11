"""
Browserless Agent - Production-Scale Browser Automation
Uses Browserless Docker service for headless Chrome automation
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any, List, Optional
from loguru import logger

class BrowserlessAgent:
    """
    Production-scale browser automation using Browserless Docker service
    Provides headless Chrome automation with API-based control
    """

    def __init__(self, endpoint: str = "http://localhost:3001"):
        """Initialize Browserless agent"""
        self.endpoint = endpoint
        self.session = None
        self.initialized = False
        logger.info(f"BrowserlessAgent initialized with endpoint: {endpoint}")

    async def initialize(self):
        """Initialize the Browserless connection"""
        try:
            self.session = aiohttp.ClientSession()
            # Test connection
            async with self.session.get(f"{self.endpoint}/health") as response:
                if response.status == 200:
                    self.initialized = True
                    logger.info("Browserless connection established")
                else:
                    logger.warning(f"Browserless health check failed: {response.status}")
        except Exception as e:
            logger.warning(f"Browserless initialization failed: {e}")
            self.initialized = False

    async def execute_script(self, script: str, url: str = None) -> Dict[str, Any]:
        """Execute JavaScript in browserless environment"""
        if not self.session:
            return {"error": "Session not initialized"}

        try:
            payload = {
                "code": script,
                "context": {}
            }
            
            if url:
                payload["url"] = url

            async with self.session.post(
                f"{self.endpoint}/function",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return {"status": "success", "result": result}
                else:
                    error_text = await response.text()
                    return {"error": f"Browserless API error: {response.status} - {error_text}"}
        except Exception as e:
            logger.error(f"Script execution failed: {e}")
            return {"error": str(e)}

    async def take_screenshot(self, url: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Take screenshot of a webpage"""
        if not self.session:
            return {"error": "Session not initialized"}

        try:
            payload = {
                "url": url,
                "options": options or {}
            }

            async with self.session.post(
                f"{self.endpoint}/screenshot",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    screenshot_data = await response.read()
                    return {"status": "success", "screenshot": screenshot_data}
                else:
                    error_text = await response.text()
                    return {"error": f"Screenshot failed: {response.status} - {error_text}"}
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            return {"error": str(e)}

    async def execute_actions(self, actions: List[Dict[str, Any]], url: str) -> Dict[str, Any]:
        """Execute a sequence of browser actions"""
        script = f"""
        const puppeteer = require('puppeteer');
        
        (async () => {{
            const browser = await puppeteer.launch();
            const page = await browser.newPage();
            await page.goto('{url}');
            
            const actions = {json.dumps(actions)};
            
            for (const action of actions) {{
                switch (action.type) {{
                    case 'click':
                        await page.click(action.selector);
                        break;
                    case 'type':
                        await page.type(action.selector, action.text);
                        break;
                    case 'wait':
                        await page.waitForSelector(action.selector);
                        break;
                    case 'screenshot':
                        await page.screenshot({{path: 'screenshot.png'}});
                        break;
                }}
                await page.waitForTimeout(1000);
            }}
            
            await browser.close();
            return {{ status: 'completed', actions_executed: actions.length }};
        }})();
        """
        
        return await self.execute_script(script, url)

    async def apply_to_job(self, job_url: str, **kwargs) -> Dict[str, Any]:
        """Apply to job using Browserless"""
        # Example action sequence for job application
        actions = [
            {"type": "wait", "selector": "body"},
            {"type": "click", "selector": "[data-testid='apply-button']"},
            {"type": "wait", "selector": ".application-form"},
            {"type": "type", "selector": "#name", "text": kwargs.get("name", "John Doe")},
            {"type": "type", "selector": "#email", "text": kwargs.get("email", "john@example.com")},
            {"type": "click", "selector": "[type='submit']"}
        ]
        
        result = await self.execute_actions(actions, job_url)
        return {"status": "success", "agent": "browserless", "job_url": job_url, "result": result}

    async def bulk_apply(self, job_urls: List[str], **kwargs) -> Dict[str, Any]:
        """Bulk apply using Browserless"""
        results = []
        for url in job_urls:
            result = await self.apply_to_job(url, **kwargs)
            results.append(result)
            await asyncio.sleep(2)  # Rate limiting
        
        return {"status": "success", "agent": "browserless", "total_jobs": len(job_urls), "results": results}

    async def cleanup(self):
        """Clean up resources"""
        if self.session:
            await self.session.close()
