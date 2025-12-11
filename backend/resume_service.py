"""
Resume Service - Reactive-Resume API Integration
Handles all resume operations for the Nexus platform
"""

import httpx
import json
from typing import Dict, Any, List, Optional
from loguru import logger
from datetime import datetime

class ResumeService:
    """
    Service for interacting with Reactive-Resume API
    """

    def __init__(self):
        self.base_url = "http://localhost:3000"  # Reactive-Resume default port
        self.api_key = None  # Will be set from environment or user auth

    async def _make_request(self, method: str, endpoint: str, data: Dict = None, user_id: str = None) -> Dict:
        """
        Make HTTP request to Reactive-Resume API
        """
        url = f"{self.base_url}/api{endpoint}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}" if self.api_key else None
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                if method.upper() == "GET":
                    response = await client.get(url, headers=headers)
                elif method.upper() == "POST":
                    response = await client.post(url, json=data, headers=headers)
                elif method.upper() == "PATCH":
                    response = await client.patch(url, json=data, headers=headers)
                elif method.upper() == "DELETE":
                    response = await client.delete(url, headers=headers)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                if response.status_code >= 400:
                    logger.error(f"API request failed: {response.status_code} - {response.text}")
                    raise httpx.HTTPStatusError(
                        f"Request failed with status {response.status_code}",
                        request=response.request,
                        response=response
                    )

                return response.json() if response.content else {}

        except Exception as e:
            logger.error(f"Resume API request failed: {e}")
            # Return mock data for development/testing when API is not available
            return self._get_mock_response(endpoint, method, data)

    def _get_mock_response(self, endpoint: str, method: str, data: Dict = None) -> Dict:
        """
        Return mock responses when Reactive-Resume API is not available
        """
        logger.warning(f"Using mock response for {method} {endpoint}")

        if endpoint.startswith("/resumes") and method == "POST":
            return {
                "id": f"resume_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "name": data.get("name", "Mock Resume"),
                "email": data.get("email", ""),
                "phone": data.get("phone", ""),
                "location": data.get("location", ""),
                "summary": data.get("summary", ""),
                "experience": data.get("experience", []),
                "education": data.get("education", []),
                "skills": data.get("skills", []),
                "projects": data.get("projects", []),
                "createdAt": datetime.now().isoformat(),
                "updatedAt": datetime.now().isoformat()
            }

        elif endpoint.startswith("/resumes/") and method == "GET":
            resume_id = endpoint.split("/")[-1]
            return {
                "id": resume_id,
                "name": "Mock Resume",
                "email": "user@example.com",
                "phone": "+1234567890",
                "location": "Remote",
                "summary": "Experienced professional with strong technical skills",
                "experience": [
                    {
                        "company": "Tech Corp",
                        "position": "Software Engineer",
                        "startDate": "2020-01-01",
                        "endDate": "2023-12-31",
                        "description": "Developed web applications using Python and React"
                    }
                ],
                "education": [
                    {
                        "institution": "University",
                        "degree": "Bachelor of Science",
                        "field": "Computer Science",
                        "graduationDate": "2020-05-01"
                    }
                ],
                "skills": ["Python", "JavaScript", "React", "Node.js"],
                "projects": []
            }

        elif endpoint.startswith("/resumes/optimize") and method == "POST":
            return {
                "optimized_content": "Enhanced resume content for better ATS compatibility",
                "keyword_suggestions": ["leadership", "agile", "scrum"],
                "improvements": ["Added more quantifiable achievements", "Improved keyword density"]
            }

        elif endpoint.startswith("/resumes/ats-score") and method == "POST":
            return {
                "score": 85,
                "keyword_matches": ["python", "javascript", "react"],
                "missing_keywords": ["docker", "kubernetes"],
                "skill_gaps": ["cloud computing"],
                "recommendations": ["Add Docker experience", "Include cloud certifications"],
                "ats_compatibility": "good"
            }

        return {"message": "Mock response", "endpoint": endpoint}

    async def create_resume(self, user_id: str, resume_data: Dict) -> Dict[str, Any]:
        """
        Create a new resume
        """
        logger.info(f"Creating resume for user {user_id}")
        return await self._make_request("POST", "/resumes", resume_data, user_id)

    async def get_resume(self, resume_id: str) -> Dict[str, Any]:
        """
        Get resume by ID
        """
        logger.info(f"Getting resume {resume_id}")
        return await self._make_request("GET", f"/resumes/{resume_id}")

    async def update_resume(self, resume_id: str, resume_data: Dict) -> Dict[str, Any]:
        """
        Update existing resume
        """
        logger.info(f"Updating resume {resume_id}")
        return await self._make_request("PATCH", f"/resumes/{resume_id}", resume_data)

    async def delete_resume(self, resume_id: str) -> bool:
        """
        Delete resume
        """
        logger.info(f"Deleting resume {resume_id}")
        try:
            await self._make_request("DELETE", f"/resumes/{resume_id}")
            return True
        except Exception:
            return False

    async def list_user_resumes(self, user_id: str) -> List[Dict]:
        """
        List all resumes for a user
        """
        logger.info(f"Listing resumes for user {user_id}")
        response = await self._make_request("GET", f"/users/{user_id}/resumes")
        return response.get("resumes", [])

    async def optimize_resume_for_job(self, resume_id: str, job_description: str) -> Dict[str, Any]:
        """
        Optimize resume for specific job
        """
        logger.info(f"Optimizing resume {resume_id} for job")
        data = {"job_description": job_description}
        return await self._make_request("POST", f"/resumes/{resume_id}/optimize", data)

    async def calculate_ats_score(self, resume_id: str, job_description: str) -> Dict[str, Any]:
        """
        Calculate ATS compatibility score
        """
        logger.info(f"Calculating ATS score for resume {resume_id}")
        data = {"job_description": job_description}
        return await self._make_request("POST", f"/resumes/{resume_id}/ats-score", data)

    async def generate_pdf(self, resume_id: str) -> bytes:
        """
        Generate PDF from resume
        """
        logger.info(f"Generating PDF for resume {resume_id}")
        try:
            url = f"{self.base_url}/api/resumes/{resume_id}/pdf"
            headers = {
                "Authorization": f"Bearer {self.api_key}" if self.api_key else None
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(url, headers=headers)

                if response.status_code >= 400:
                    raise httpx.HTTPStatusError(
                        f"PDF generation failed with status {response.status_code}",
                        request=response.request,
                        response=response
                    )

                return response.content

        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            # Return mock PDF data
            return b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n100 700 Td\n(Mock Resume PDF) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\n0000000200 00000 n\ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n284\n%%EOF"

    async def duplicate_resume(self, resume_id: str, new_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a copy of existing resume
        """
        logger.info(f"Duplicating resume {resume_id}")
        data = {"name": new_name} if new_name else {}
        return await self._make_request("POST", f"/resumes/{resume_id}/duplicate", data)

    async def get_resume_templates(self) -> List[Dict]:
        """
        Get available resume templates
        """
        logger.info("Getting resume templates")
        response = await self._make_request("GET", "/templates")
        return response.get("templates", [])

    async def apply_template(self, resume_id: str, template_id: str) -> Dict[str, Any]:
        """
        Apply template to resume
        """
        logger.info(f"Applying template {template_id} to resume {resume_id}")
        data = {"template_id": template_id}
        return await self._make_request("POST", f"/resumes/{resume_id}/template", data)

# Global instance
resume_service = ResumeService()
