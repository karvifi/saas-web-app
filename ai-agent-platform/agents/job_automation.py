"""
Job Application Automation - Auto-apply with browser agent
"""

from typing import Dict, Any, List
from loguru import logger
from agents.browser_advanced import advanced_browser_agent

class JobAutomation:
    """
    Automates job applications across multiple platforms
    """
    
    def __init__(self):
        self.browser = advanced_browser_agent
    
    async def auto_apply_linkedin(self, job_url: str, user_profile: Dict) -> Dict[str, Any]:
        """
        Auto-apply to LinkedIn Easy Apply jobs
        """
        logger.info(f"🤖 Auto-applying to LinkedIn job: {job_url}")
        
        try:
            await self.browser.initialize()
            
            # Navigate to job
            await self.browser.navigate_and_wait(job_url)
            
            # Click Easy Apply button
            await self.browser.click_button("Easy Apply")
            await self.browser.page.wait_for_timeout(2000)
            
            # Fill application form
            form_data = {
                "firstName": user_profile.get("first_name", ""),
                "lastName": user_profile.get("last_name", ""),
                "email": user_profile.get("email", ""),
                "phone": user_profile.get("phone", "")
            }
            
            await self.browser.fill_form(form_data)
            
            # Handle multi-page forms
            while True:
                # Check for Next button
                next_button = await self.browser.page.query_selector('button[aria-label="Continue to next step"]')
                if next_button:
                    await next_button.click()
                    await self.browser.page.wait_for_timeout(1000)
                else:
                    break
            
            # Submit application
            submit_button = await self.browser.page.query_selector('button[aria-label="Submit application"]')
            if submit_button:
                await submit_button.click()
                logger.info("✅ Application submitted!")
                
                return {
                    "status": "success",
                    "platform": "LinkedIn",
                    "job_url": job_url,
                    "message": "Application submitted successfully"
                }
            
        except Exception as e:
            logger.error(f"Auto-apply failed: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
        
        finally:
            await self.browser.close()
    
    async def bulk_apply(self, jobs: List[Dict], user_profile: Dict) -> Dict[str, Any]:
        """
        Apply to multiple jobs automatically
        """
        results = {
            "total": len(jobs),
            "successful": 0,
            "failed": 0,
            "details": []
        }
        
        for job in jobs:
            if "linkedin.com" in job.get('url', ''):
                result = await self.auto_apply_linkedin(job['url'], user_profile)
                
                if result['status'] == "success":
                    results['successful'] += 1
                else:
                    results['failed'] += 1
                
                results['details'].append(result)
        
        return results

# Global instance
job_automation = JobAutomation()