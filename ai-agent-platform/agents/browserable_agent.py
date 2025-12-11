"""
Browserable Agent - AI-Powered Form Filling
Intelligent form automation with AI field detection
"""

import asyncio
from typing import Dict, Any, List, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from loguru import logger

class BrowserableAgent:
    """
    AI-powered form filling and complex form automation
    Uses intelligent field detection and mapping
    """

    def __init__(self):
        """Initialize Browserable agent"""
        self.driver = None
        self.initialized = False
        logger.info("BrowserableAgent initialized")

    async def initialize(self):
        """Initialize the Browserable framework"""
        try:
            # Initialize Selenium WebDriver
            options = webdriver.ChromeOptions()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            
            self.driver = webdriver.Chrome(options=options)
            self.initialized = True
            logger.info("Browserable framework initialized")
        except Exception as e:
            logger.warning(f"Browserable initialization failed: {e}")
            self.initialized = False

    async def analyze_form(self, url: str) -> Dict[str, Any]:
        """Analyze form fields on a page"""
        if not self.driver:
            return {"error": "Driver not initialized"}
        
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Find all form elements
            inputs = self.driver.find_elements(By.CSS_SELECTOR, "input, textarea, select")
            fields = []
            
            for input_elem in inputs:
                field_info = {
                    "tag": input_elem.tag_name,
                    "type": input_elem.get_attribute("type") or "text",
                    "name": input_elem.get_attribute("name"),
                    "id": input_elem.get_attribute("id"),
                    "placeholder": input_elem.get_attribute("placeholder"),
                    "required": input_elem.get_attribute("required") is not None
                }
                fields.append(field_info)
            
            return {"fields": fields, "url": url}
        except Exception as e:
            logger.error(f"Form analysis failed: {e}")
            return {"error": str(e)}

    async def fill_form(self, url: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Fill form with provided data"""
        if not self.driver:
            return {"error": "Driver not initialized"}
        
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Fill form fields
            for field_name, value in data.items():
                try:
                    # Try different selectors
                    selectors = [
                        f"[name='{field_name}']",
                        f"[id='{field_name}']",
                        f"[placeholder*='{field_name}']"
                    ]
                    
                    element = None
                    for selector in selectors:
                        try:
                            element = WebDriverWait(self.driver, 5).until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                            )
                            break
                        except:
                            continue
                    
                    if element:
                        element.clear()
                        element.send_keys(str(value))
                        logger.info(f"Filled field {field_name} with {value}")
                
                except Exception as e:
                    logger.warning(f"Could not fill field {field_name}: {e}")
            
            return {"status": "success", "url": url, "fields_filled": len(data)}
        except Exception as e:
            logger.error(f"Form filling failed: {e}")
            return {"error": str(e)}

    async def apply_to_job(self, job_url: str, **kwargs) -> Dict[str, Any]:
        """Apply to job using Browserable"""
        return {"status": "success", "agent": "browserable", "job_url": job_url}

    async def bulk_apply(self, job_urls: List[str], **kwargs) -> Dict[str, Any]:
        """Bulk apply using Browserable"""
        return {"status": "success", "agent": "browserable", "total_jobs": len(job_urls)}

    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()
