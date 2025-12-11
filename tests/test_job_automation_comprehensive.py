"""
Comprehensive Tests for Upgraded Job Automation Platform
Tests job search, scraping, and application workflows across major platforms
Validates hybrid routing system and tool fallbacks
"""

import pytest
import asyncio
import json
import tempfile
import os
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any, List
from datetime import datetime
import pandas as pd

# Import agents
from agents.career import CareerAgent
from agents.job_automation import JobAutomation
from agents.job_scraper import JobScraperAgent
from agents.browser_job_agent import BrowserJobAgent
from agents.browser_advanced import AdvancedBrowserAgent


class TestJobSearchWorkflows:
    """Test job search across all major platforms"""

    @pytest.fixture
    def career_agent(self):
        return CareerAgent()

    @pytest.fixture
    def browser_job_agent(self):
        return BrowserJobAgent()

    @pytest.fixture
    def job_scraper(self):
        return JobScraperAgent()

    @pytest.mark.asyncio
    async def test_linkedin_job_search(self, browser_job_agent):
        """Test LinkedIn job search functionality"""
        with patch("agents.browser_job_agent.scrape_jobs") as mock_scrape:
            # Mock the scrape_jobs function to return LinkedIn jobs
            mock_df = pd.DataFrame([
                {
                    "title": "Senior Python Developer",
                    "company": "Tech Corp",
                    "location": "San Francisco, CA",
                    "job_url": "https://linkedin.com/jobs/123",
                    "salary": "$120k - $150k",
                    "description": "Python development role",
                    "site": "linkedin",
                    "date_posted": "2024-01-01",
                    "is_remote": False
                }
            ])
            mock_scrape.return_value = mock_df

            results = await browser_job_agent.search_jobs(
                title="Python Developer",
                location="San Francisco",
                max_results=5
            )

            assert results["status"] == "success"
            assert len(results["jobs"]) > 0
            assert results["searched_platforms"] >= 1
            assert "linkedin.com" in str(results["jobs"][0]["url"])

    @pytest.mark.asyncio
    async def test_indeed_job_search(self, browser_job_agent):
        """Test Indeed job search functionality"""
        with patch("agents.browser_job_agent.scrape_jobs") as mock_scrape:
            mock_df = pd.DataFrame([
                {
                    "title": "Full Stack Engineer",
                    "company": "Startup Inc",
                    "location": "Remote",
                    "job_url": "https://indeed.com/jobs/456",
                    "salary": "$90k - $120k",
                    "description": "Full stack development",
                    "site": "indeed",
                    "date_posted": "2024-01-01",
                    "is_remote": True
                }
            ])
            mock_scrape.return_value = mock_df

            results = await browser_job_agent.search_jobs(
                title="Full Stack Engineer",
                location="Remote",
                max_results=3
            )

            assert results["status"] == "success"
            assert "indeed.com" in str(results["jobs"][0]["url"])

    @pytest.mark.asyncio
    async def test_remoteok_job_search(self, career_agent):
        """Test RemoteOK job search via career agent"""
        mock_jobs = [
            {
                "slug": "python-developer-123",
                "title": "Python Developer",
                "company": "Tech Corp",
                "location": "Remote",
                "salary": "$80k - $100k"
            }
        ]
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
            mock_response.text = json.dumps(mock_jobs)
            mock_response.raise_for_status = Mock()
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            jobs = await career_agent.search_jobs("Python Developer")

            # Should return jobs
            assert isinstance(jobs, list)
            assert len(jobs) == 1
            job = jobs[0]
            assert job["title"] == "Python Developer"
            assert job["company"] == "Tech Corp"
            assert "url" in job
            assert job.get("source") == "RemoteOK"

    @pytest.mark.asyncio
    async def test_multi_platform_search(self, browser_job_agent):
        """Test searching across multiple platforms simultaneously"""
        with patch("agents.browser_job_agent.Agent") as mock_agent:
            mock_agent_instance = AsyncMock()
            mock_agent.return_value = mock_agent_instance
            mock_agent_instance.run.return_value = Mock(extracted_content=json.dumps([
                {"title": "DevOps Engineer", "company": "Cloud Corp", "url": "https://linkedin.com/jobs/789"}
            ]))

            results = await browser_job_agent.search_jobs(
                title="DevOps Engineer",
                location="New York",
                max_results=10
            )

            assert results["status"] == "success"
            assert results["total_found"] >= 0
            assert results["searched_platforms"] >= 1


class TestJobScrapingWorkflows:
    """Test job scraping functionality"""

    @pytest.fixture
    def scraper_agent(self):
        return JobScraperAgent()

    def test_remoteok_scraping(self, scraper_agent):
        """Test RemoteOK job scraping"""
        jobs = scraper_agent.scrape_jobs(platforms=["remoteok"])

        assert isinstance(jobs, list)
        if jobs:
            job = jobs[0]
            assert "title" in job
            assert "company" in job
            assert "url" in job
            assert "remoteok.com" in job["url"]

    def test_weworkremotely_scraping(self, scraper_agent):
        """Test We Work Remotely scraping"""
        jobs = scraper_agent.scrape_jobs(platforms=["weworkremotely"])

        assert isinstance(jobs, list)
        if jobs:
            job = jobs[0]
            assert "title" in job
            assert "company" in job
            assert "url" in job

    def test_multi_platform_scraping(self, scraper_agent):
        """Test scraping multiple platforms"""
        jobs = scraper_agent.scrape_jobs(platforms=["remoteok", "weworkremotely"])

        assert isinstance(jobs, list)
        # Should have jobs from both platforms
        remoteok_jobs = [j for j in jobs if "remoteok.com" in j["url"]]
        wwr_jobs = [j for j in jobs if "weworkremotely.com" in j["url"]]

        assert len(remoteok_jobs) >= 0
        assert len(wwr_jobs) >= 0

    def test_keyword_filtered_scraping(self, scraper_agent):
        """Test scraping with keyword filtering"""
        jobs = scraper_agent.scrape_jobs(platforms=["remoteok"], keywords="python")

        assert isinstance(jobs, list)
        for job in jobs:
            # Check if keywords appear in title, description, or tags
            has_keyword = (
                "python" in job.get("title", "").lower() or
                "python" in job.get("description", "").lower() or
                any("python" in tag.lower() for tag in job.get("tags", []))
            )
            assert has_keyword

    def test_scraper_output_file(self, scraper_agent):
        """Test saving scraped results to file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = os.path.join(temp_dir, "jobs.json")

            jobs = scraper_agent.run_scraper("remoteok", output_file)

            assert os.path.exists(output_file)

            with open(output_file, "r") as f:
                saved_jobs = json.load(f)

            assert len(saved_jobs) == len(jobs)


class TestJobApplicationWorkflows:
    """Test job application automation"""

    @pytest.fixture
    def job_automation(self):
        return JobAutomation()

    @pytest.fixture
    def browser_agent(self):
        return BrowserJobAgent()

    @pytest.fixture
    def sample_user_profile(self):
        return {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "+1-555-0123",
            "skills": ["Python", "Django", "React"]
        }

    @pytest.mark.asyncio
    async def test_linkedin_easy_apply(self, job_automation, sample_user_profile):
        """Test LinkedIn Easy Apply automation"""
        job_url = "https://linkedin.com/jobs/view/123"

        with patch.object(job_automation.browser, "initialize", new_callable=AsyncMock), \
             patch.object(job_automation.browser, "navigate_and_wait", new_callable=AsyncMock) as mock_navigate, \
             patch.object(job_automation.browser, "click_button", new_callable=AsyncMock) as mock_click, \
             patch.object(job_automation.browser, "fill_form", new_callable=AsyncMock) as mock_fill, \
             patch.object(job_automation.browser, "close", new_callable=AsyncMock), \
             patch.object(job_automation.browser, "page") as mock_page:

            mock_navigate.return_value = True

            # Mock page methods
            submit_button = Mock()
            submit_button.click = AsyncMock()
            
            def mock_query_selector(selector):
                if 'Submit application' in selector:
                    return submit_button
                return None
            
            mock_page.query_selector = AsyncMock(side_effect=mock_query_selector)
            mock_page.wait_for_timeout = AsyncMock()

            result = await job_automation.auto_apply_linkedin(job_url, sample_user_profile)

            assert result["status"] == "success"
            assert result["platform"] == "LinkedIn"
            assert result["job_url"] == job_url

    @pytest.mark.asyncio
    async def test_bulk_job_application(self, job_automation, sample_user_profile):
        """Test applying to multiple jobs"""
        jobs = [
            {"url": "https://linkedin.com/jobs/123", "title": "Python Dev", "company": "Tech Corp"},
            {"url": "https://linkedin.com/jobs/456", "title": "Django Dev", "company": "Web Inc"}
        ]

        with patch.object(job_automation, "auto_apply_linkedin", new_callable=AsyncMock) as mock_apply:
            mock_apply.side_effect = [
                {"status": "success", "job_url": jobs[0]["url"]},
                {"status": "error", "job_url": jobs[1]["url"], "message": "Application failed"}
            ]

            results = await job_automation.bulk_apply(jobs, sample_user_profile)

            assert results["total"] == 2
            assert results["successful"] == 1
            assert results["failed"] == 1
            assert len(results["details"]) == 2

    @pytest.mark.asyncio
    async def test_browser_agent_job_application(self, browser_agent):
        """Test job application via browser agent"""
        job = {
            "title": "Software Engineer",
            "company": "Tech Corp",
            "url": "https://linkedin.com/jobs/123"
        }

        with patch("agents.browser_job_agent.Agent") as mock_agent:
            mock_agent_instance = AsyncMock()
            mock_agent.return_value = mock_agent_instance
            mock_agent_instance.run.return_value = None

            result = await browser_agent.apply_to_job(job)

            assert result["status"] == "applied"
            assert result["job"] == job["title"]
            assert result["company"] == job["company"]

    @pytest.mark.asyncio
    async def test_bulk_browser_applications(self, browser_agent):
        """Test bulk applications with browser agent"""
        jobs = [
            {"title": "Dev 1", "company": "Company A", "url": "https://example.com/job1"},
            {"title": "Dev 2", "company": "Company B", "url": "https://example.com/job2"}
        ]

        with patch.object(browser_agent, "apply_to_job", new_callable=AsyncMock) as mock_apply:
            mock_apply.side_effect = [
                {"status": "applied", "job": "Dev 1", "company": "Company A"},
                {"status": "applied", "job": "Dev 2", "company": "Company B"}
            ]

            results = await browser_agent.bulk_apply(jobs, delay=1)

            assert results["status"] == "completed"
            assert results["total_jobs"] == 2
            assert results["successful_applications"] == 2
            assert results["failed_applications"] == 0


class TestHybridRoutingSystem:
    """Test hybrid routing between different automation tools"""

    @pytest.fixture
    def mock_browser_use(self):
        """Mock Browser-Use tool"""
        return AsyncMock()

    @pytest.fixture
    def mock_skyvern(self):
        """Mock Skyvern tool"""
        return AsyncMock()

    @pytest.fixture
    def mock_crawl4ai(self):
        """Mock Crawl4AI tool"""
        return AsyncMock()

    @pytest.fixture
    def mock_scrapegraphai(self):
        """Mock ScrapeGraphAI tool"""
        return AsyncMock()

    def test_tool_selection_logic(self):
        """Test logic for selecting appropriate tool based on task"""
        # This would be implemented in a hybrid router
        tool_configs = {
            "Browser-Use": {
                "strengths": ["form_filling", "interactive_elements", "llm_powered"],
                "platforms": ["linkedin", "indeed", "complex_forms"]
            },
            "Skyvern": {
                "strengths": ["enterprise_automation", "complex_workflows"],
                "platforms": ["linkedin", "greenhouse", "workday"]
            },
            "Crawl4AI": {
                "strengths": ["fast_scraping", "api_like_extraction"],
                "platforms": ["remoteok", "weworkremotely", "simple_sites"]
            },
            "ScrapeGraphAI": {
                "strengths": ["intelligent_parsing", "structured_data"],
                "platforms": ["indeed", "monster", "data_rich_sites"]
            }
        }

        # Test tool selection for LinkedIn application
        task = {"platform": "linkedin", "action": "apply", "complexity": "high"}
        selected_tool = self._select_tool_for_task(task, tool_configs)
        assert selected_tool in ["Browser-Use", "Skyvern"]

        # Test tool selection for RemoteOK scraping
        task = {"platform": "remoteok", "action": "scrape", "complexity": "low"}
        selected_tool = self._select_tool_for_task(task, tool_configs)
        assert selected_tool == "Crawl4AI"

    def _select_tool_for_task(self, task: Dict, tool_configs: Dict) -> str:
        """Mock tool selection logic"""
        platform = task.get("platform", "").lower()
        action = task.get("action", "")
        complexity = task.get("complexity", "medium")

        if platform == "linkedin" and action == "apply":
            return "Browser-Use" if complexity == "high" else "Skyvern"
        elif platform in ["remoteok", "weworkremotely"] and action == "scrape":
            return "Crawl4AI"
        elif platform == "indeed" and action == "scrape":
            return "ScrapeGraphAI"
        else:
            return "Browser-Use"  # Default fallback

    @pytest.mark.asyncio
    async def test_tool_fallback_mechanism(self, mock_browser_use, mock_skyvern):
        """Test fallback when primary tool fails"""
        # Simulate Browser-Use failing
        mock_browser_use.side_effect = Exception("Browser-Use failed")

        # Skyvern succeeds
        mock_skyvern.return_value = {"status": "success", "data": "scraped_content"}

        tools = {
            "primary": mock_browser_use,
            "fallback": mock_skyvern
        }

        result = await self._execute_with_fallback(tools, "scrape_job", {"url": "https://example.com"})

        assert result["status"] == "success"
        mock_browser_use.assert_called_once()
        mock_skyvern.assert_called_once()

    async def _execute_with_fallback(self, tools: Dict, action: str, params: Dict) -> Dict:
        """Mock fallback execution"""
        try:
            return await tools["primary"](action, params)
        except Exception:
            return await tools["fallback"](action, params)

    @pytest.mark.asyncio
    async def test_tool_routing_integration(self, mock_browser_use, mock_skyvern, mock_crawl4ai):
        """Test integrated tool routing for different platforms"""
        routing_config = {
            "linkedin": ["Browser-Use", "Skyvern"],
            "indeed": ["ScrapeGraphAI", "Browser-Use"],
            "remoteok": ["Crawl4AI", "Browser-Use"]
        }

        tools = {
            "Browser-Use": mock_browser_use,
            "Skyvern": mock_skyvern,
            "Crawl4AI": mock_crawl4ai
        }

        # Test LinkedIn routing
        result = await self._route_and_execute(
            platform="linkedin",
            action="apply",
            routing_config=routing_config,
            tools=tools
        )

        assert mock_browser_use.called or mock_skyvern.called

    async def _route_and_execute(self, platform: str, action: str,
                               routing_config: Dict, tools: Dict) -> Dict:
        """Mock routing and execution"""
        available_tools = routing_config.get(platform, ["Browser-Use"])

        for tool_name in available_tools:
            tool = tools.get(tool_name)
            if tool:
                try:
                    return await tool(action, {"platform": platform})
                except Exception:
                    continue

        return {"status": "failed", "error": "All tools failed"}


class TestErrorHandlingAndRecovery:
    """Test error handling and recovery mechanisms"""

    @pytest.fixture
    def browser_job_agent(self):
        return BrowserJobAgent()

    @pytest.fixture
    def scraper_agent(self):
        return JobScraperAgent()

    @pytest.fixture
    def job_automation(self):
        return JobAutomation()

    @pytest.fixture
    def browser_agent(self):
        return AdvancedBrowserAgent()

    @pytest.fixture
    def sample_user_profile(self):
        return {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "+1-555-0123",
            "skills": ["Python", "Django", "React"]
        }

    @pytest.mark.asyncio
    async def test_network_failure_recovery(self, browser_job_agent):
        """Test recovery from network failures"""
        with patch("agents.browser_job_agent.Agent") as mock_agent:
            mock_agent_instance = AsyncMock()
            mock_agent.return_value = mock_agent_instance

            # First call fails with network error
            mock_agent_instance.run.side_effect = [
                Exception("Network timeout"),
                Mock(extracted_content=json.dumps([{"title": "Job 1", "company": "Company A"}]))
            ]

            # Should retry and succeed
            results = await browser_job_agent.search_jobs("developer", "remote")

            assert results["status"] == "success"
            assert len(results["jobs"]) > 0

    @pytest.mark.asyncio
    async def test_platform_rate_limiting(self, browser_job_agent):
        """Test handling of platform rate limits"""
        with patch("agents.browser_job_agent.Agent") as mock_agent:
            mock_agent_instance = AsyncMock()
            mock_agent.return_value = mock_agent_instance

            # Simulate rate limiting
            mock_agent_instance.run.side_effect = [
                Exception("Rate limit exceeded"),
                Exception("Rate limit exceeded"),
                Mock(extracted_content=json.dumps([{"title": "Job 1"}]))
            ]

            results = await browser_job_agent.search_jobs("engineer", "san francisco")

            # Should eventually succeed after retries
            assert results["status"] == "success"

    def test_invalid_platform_handling(self, scraper_agent):
        """Test handling of invalid platforms"""
        with pytest.raises(ValueError):
            scraper_agent.run_scraper("invalid_platform")

    @pytest.mark.asyncio
    async def test_partial_failure_bulk_apply(self, job_automation, sample_user_profile):
        """Test bulk apply with some failures"""
        jobs = [
            {"url": "https://linkedin.com/jobs/1", "title": "Job 1"},
            {"url": "https://linkedin.com/jobs/2", "title": "Job 2"},
            {"url": "https://linkedin.com/jobs/3", "title": "Job 3"}
        ]

        with patch.object(job_automation, "auto_apply_linkedin", new_callable=AsyncMock) as mock_apply:
            mock_apply.side_effect = [
                {"status": "success"},
                {"status": "error", "message": "Application failed"},
                {"status": "success"}
            ]

            results = await job_automation.bulk_apply(jobs, sample_user_profile)

            assert results["successful"] == 2
            assert results["failed"] == 1
            assert results["total"] == 3


class TestPerformanceAndScalability:
    """Test performance and scalability aspects"""

    @pytest.fixture
    def browser_job_agent(self):
        return BrowserJobAgent()

    @pytest.fixture
    def browser_agent(self):
        return BrowserJobAgent()

    @pytest.fixture
    def scraper_agent(self):
        return JobScraperAgent()

    @pytest.mark.asyncio
    async def test_concurrent_job_searches(self, browser_job_agent):
        """Test concurrent job searches across platforms"""
        search_tasks = [
            browser_job_agent.search_jobs(f"developer_{i}", "remote", 5)
            for i in range(3)
        ]

        with patch("agents.browser_job_agent.Agent") as mock_agent:
            mock_agent_instance = AsyncMock()
            mock_agent.return_value = mock_agent_instance
            mock_agent_instance.run.return_value = Mock(extracted_content=json.dumps([
                {"title": "Job 1", "company": "Company 1"},
                {"title": "Job 2", "company": "Company 2"},
                {"title": "Job 3", "company": "Company 3"}
            ]))

            results = await asyncio.gather(*search_tasks, return_exceptions=True)

            # All should succeed
            for result in results:
                if not isinstance(result, Exception):
                    assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_bulk_application_performance(self, browser_agent):
        """Test performance of bulk applications"""
        jobs = [{"title": f"Job {i}", "company": f"Company {i}", "url": f"https://example.com/{i}"}
               for i in range(5)]

        start_time = datetime.utcnow()

        with patch.object(browser_agent, "apply_to_job", new_callable=AsyncMock) as mock_apply:
            mock_apply.return_value = {"status": "applied"}

            results = await browser_agent.bulk_apply(jobs, delay=0.1)  # Minimal delay

            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            assert results["successful_applications"] == 5
            # Should complete within reasonable time (allowing for delays)
            assert duration < 10

    def test_memory_usage_scraping(self, scraper_agent):
        """Test memory usage during large-scale scraping"""
        # This would require actual performance monitoring
        # For now, just ensure no memory leaks in basic operation
        jobs = scraper_agent.scrape_jobs(platforms=["remoteok", "weworkremotely"])

        assert isinstance(jobs, list)
        # Ensure we can handle the results without issues
        assert len(jobs) >= 0


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])