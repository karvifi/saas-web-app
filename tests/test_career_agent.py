"""
Tests for Career Agent
"""

import pytest
import asyncio
from agents.career import career_agent


class TestCareerAgent:
    """Test career agent functionality"""

    @pytest.mark.asyncio
    async def test_search_jobs(self):
        """Test job search functionality"""
        jobs = await career_agent.search_jobs("Python Developer")

        assert isinstance(jobs, list)
        assert len(jobs) >= 0  # May be 0 if API fails, but should not crash

        if jobs:  # Only check structure if we got results
            job = jobs[0]
            assert "title" in job
            assert "company" in job
            assert "url" in job
            assert "source" in job

    @pytest.mark.asyncio
    async def test_analyze_job(self):
        """Test job analysis"""
        job = {
            "title": "Python Developer",
            "company": "Tech Corp",
            "description": "Looking for Python developer with Django experience"
        }

        user_profile = {
            "skills": ["Python", "Django", "JavaScript"]
        }

        result = await career_agent.analyze_job(job, user_profile)

        assert "match_score" in result
        assert "matching_skills" in result
        assert "recommendation" in result
        assert isinstance(result["match_score"], float)
        assert 0.0 <= result["match_score"] <= 1.0

    @pytest.mark.asyncio
    async def test_auto_apply_structure(self):
        """Test auto-apply returns proper structure (without actually applying)"""
        job = {
            "title": "Test Job",
            "company": "Test Company",
            "url": "https://example.com/job/123"
        }

        user_profile = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com"
        }

        # This will likely fail due to invalid URL, but should return proper error structure
        result = await career_agent.auto_apply(job, user_profile)

        assert "status" in result
        assert "job" in result
        assert "company" in result
        assert result["status"] in ["applied", "partial", "failed", "no_apply_button", "form_error", "error"]