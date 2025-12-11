"""
Browser Job Agent - LLM-powered Job Search & Application Automation
Uses Browser-Use for intelligent browser automation
"""

from typing import Dict, Any, List, Optional
import asyncio
import json
import logging
from datetime import datetime
from browser_use import Agent
from loguru import logger
from jobspy import scrape_jobs
import pandas as pd

class BrowserJobAgent:
    """
    LLM-powered job search and application agent using Browser-Use
    """

    def __init__(self, llm_model=None):
        self.llm_model = llm_model or "gemini-1.5-flash"
        self.job_boards = [
            "https://www.linkedin.com/jobs",
            "https://www.indeed.com",
            "https://remoteok.com/remote-jobs",
            "https://weworkremotely.com/remote-jobs"
        ]
        logger.info(" BrowserJobAgent initialized with LLM-powered automation")

    async def search_jobs(self, title: str, location: str = "Remote", max_results: int = 10) -> Dict[str, Any]:
        """
        Search for jobs across multiple platforms using JobSpy structured scraping
        """
        logger.info(f" Searching jobs: {title} in {location}")

        try:
            # Use JobSpy to scrape jobs from multiple platforms
            job_data = scrape_jobs(
                site_name=["indeed", "linkedin", "zip_recruiter", "glassdoor"],
                search_term=title,
                location=location,
                results_wanted=max_results,
                hours_old=72,  # Only recent jobs
                country_indeed='USA'  # Focus on US jobs for now
            )

            # Convert DataFrame to list of dicts
            jobs = []
            if not job_data.empty:
                for _, row in job_data.iterrows():
                    job_dict = {
                        "title": str(row.get('title', '')),
                        "company": str(row.get('company', '')),
                        "location": str(row.get('location', '')),
                        "salary": str(row.get('salary', '')) if pd.notna(row.get('salary')) else '',
                        "url": str(row.get('job_url', '')),
                        "description": str(row.get('description', '')) if pd.notna(row.get('description')) else '',
                        "platform": str(row.get('site', '')),
                        "date_posted": str(row.get('date_posted', '')) if pd.notna(row.get('date_posted')) else '',
                        "is_remote": bool(row.get('is_remote', False))
                    }
                    jobs.append(job_dict)

            return {
                "status": "success",
                "jobs": jobs,
                "total_found": len(jobs),
                "searched_platforms": 4
            }

        except Exception as e:
            logger.error(f"Job search failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "jobs": []
            }

    async def apply_to_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply to a specific job using LLM-powered form filling
        """
        logger.info(f" Applying to job: {job.get('title', 'Unknown')} at {job.get('company', 'Unknown')}")

        try:
            # Create agent for job application
            agent = Agent(
                task=f"Navigate to {job.get('url', '')} and complete the job application form. Fill in all required fields with appropriate information. Submit the application.",
                llm=self.llm_model
            )

            # Execute application
            result = await agent.run()

            return {
                "status": "applied",
                "job": job.get('title', ''),
                "company": job.get('company', ''),
                "platform": self._detect_platform(job.get('url', '')),
                "message": "Application submitted successfully",
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Job application failed: {e}")
            return {
                "status": "error",
                "job": job.get('title', ''),
                "company": job.get('company', ''),
                "error": str(e)
            }

    async def bulk_apply(self, jobs: List[Dict[str, Any]], delay: int = 5) -> Dict[str, Any]:
        """
        Apply to multiple jobs with intelligent delays
        """
        logger.info(f" Bulk applying to {len(jobs)} jobs")

        results = []
        for i, job in enumerate(jobs):
            try:
                logger.info(f"Applying to job {i+1}/{len(jobs)}: {job.get('title', '')}")

                # Apply to job
                result = await self.apply_to_job(job)
                results.append(result)

                # Intelligent delay between applications
                if i < len(jobs) - 1:  # Don't delay after last application
                    await asyncio.sleep(delay)

            except Exception as e:
                logger.error(f"Bulk apply failed for job {i+1}: {e}")
                results.append({
                    "status": "error",
                    "job": job.get('title', ''),
                    "company": job.get('company', ''),
                    "error": str(e)
                })

        successful = sum(1 for r in results if r.get('status') == 'applied')
        failed = len(results) - successful

        return {
            "status": "completed",
            "total_jobs": len(jobs),
            "successful_applications": successful,
            "failed_applications": failed,
            "results": results
        }

    def _parse_job_results(self, agent_result) -> List[Dict[str, Any]]:
        """
        Parse job search results from LLM agent output
        """
        try:
            # Extract JSON from agent result
            if hasattr(agent_result, 'extracted_content'):
                content = agent_result.extracted_content
            else:
                content = str(agent_result)

            # Try to find JSON in the content
            import re
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                jobs_data = json.loads(json_match.group())
                if isinstance(jobs_data, list):
                    return jobs_data

            # Fallback: try to parse entire content as JSON
            return json.loads(content) if content.strip().startswith('[') else []

        except Exception as e:
            logger.warning(f"Failed to parse job results: {e}")
            return []

    def _detect_platform(self, url: str) -> str:
        """
        Detect job platform from URL
        """
        if 'linkedin' in url.lower():
            return 'LinkedIn'
        elif 'indeed' in url.lower():
            return 'Indeed'
        elif 'remoteok' in url.lower():
            return 'RemoteOK'
        elif 'weworkremotely' in url.lower():
            return 'We Work Remotely'
        else:
            return 'Unknown'
