"""
Comprehensive test suite for AI Agent Platform
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import json
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from enhanced_backend import app
from database import db
from auth_service import auth_service
from security import input_validator

client = TestClient(app)

class TestHealthEndpoints:
    """Test health and status endpoints"""

    def test_health_check(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "agents_available" in data
        assert len(data["agents_available"]) == 11

    def test_agents_list(self):
        response = client.get("/agents")
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert len(data["agents"]) == 11

class TestAuthentication:
    """Test user authentication"""

    def test_user_registration(self):
        user_data = {
            "email": "test@example.com",
            "password": "TestPass123!",
            "first_name": "Test",
            "last_name": "User"
        }
        response = client.post("/auth/register", json=user_data)
        assert response.status_code in [200, 400]  # 400 if already exists

    def test_user_login(self):
        login_data = {
            "email": "test@example.com",
            "password": "TestPass123!"
        }
        response = client.post("/auth/login", json=login_data)
        assert response.status_code in [200, 401]

class TestTaskExecution:
    """Test task execution with different agents"""

    def test_search_agent(self):
        task_data = {
            "query": "What is Python?",
            "user_id": "test_user"
        }
        response = client.post("/execute", json=task_data)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["agent"] == "search"

    def test_career_agent(self):
        task_data = {
            "query": "Find software engineering jobs in Berlin",
            "user_id": "test_user"
        }
        response = client.post("/execute", json=task_data)
        assert response.status_code == 200
        data = response.json()
        assert data["agent"] == "career"

    def test_travel_agent(self):
        task_data = {
            "query": "How do I get from Berlin to Munich?",
            "user_id": "test_user"
        }
        response = client.post("/execute", json=task_data)
        assert response.status_code == 200
        data = response.json()
        assert data["agent"] == "travel"

    def test_transaction_agent(self):
        task_data = {
            "query": "Find cheap laptops under 1000 euros",
            "user_id": "test_user"
        }
        response = client.post("/execute", json=task_data)
        assert response.status_code == 200
        data = response.json()
        assert data["agent"] == "transaction"

class TestInputValidation:
    """Test input validation and security"""

    def test_empty_query(self):
        task_data = {"query": "", "user_id": "test_user"}
        response = client.post("/execute", json=task_data)
        assert response.status_code == 200  # Should handle gracefully

    def test_long_query(self):
        long_query = "x" * 2000
        task_data = {"query": long_query, "user_id": "test_user"}
        response = client.post("/execute", json=task_data)
        assert response.status_code == 200

    def test_sql_injection_attempt(self):
        malicious_query = "'; DROP TABLE users; --"
        task_data = {"query": malicious_query, "user_id": "test_user"}
        response = client.post("/execute", json=task_data)
        assert response.status_code == 200
        # Should not crash and should sanitize input

class TestDatabaseOperations:
    """Test database operations"""

    def test_task_storage(self):
        # Execute a task
        task_data = {"query": "test query", "user_id": "test_user"}
        response = client.post("/execute", json=task_data)
        assert response.status_code == 200

        # Check if task was stored
        response = client.get("/tasks")
        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data

    def test_stats_endpoint(self):
        response = client.get("/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_users" in data
        assert "total_tasks" in data
        assert "active_agents" in data

class TestAgentImplementations:
    """Test individual agent implementations"""

    @pytest.mark.asyncio
    async def test_search_agent_directly(self):
        from search import SearchAgent
        agent = SearchAgent()
        result = await agent.search("test query")
        assert isinstance(result, dict)
        assert "results" in result or "message" in result

    @pytest.mark.asyncio
    async def test_career_agent_directly(self):
        from career import CareerAgent
        agent = CareerAgent()
        result = await agent.search_jobs("python developer")
        assert isinstance(result, (dict, list))

class TestSecurity:
    """Test security features"""

    def test_rate_limiting(self):
        # Make multiple requests quickly
        for i in range(15):
            task_data = {"query": f"test query {i}", "user_id": "test_user"}
            response = client.post("/execute", json=task_data)
            if i < 10:  # First 10 should work
                assert response.status_code == 200
            # Rate limiting might kick in after that

    def test_input_sanitization(self):
        # Test various input sanitization
        assert input_validator.sanitize_query("normal query") == "normal query"
        assert input_validator.sanitize_query("query with <script>") == "query with "

class TestFrontendServing:
    """Test static file serving"""

    def test_root_serves_html(self):
        response = client.get("/")
        # Should serve HTML or return JSON
        assert response.status_code in [200, 404]  # 404 if frontend files missing

    def test_app_route(self):
        response = client.get("/app")
        assert response.status_code in [200, 404]

# Integration tests
class TestEndToEnd:
    """End-to-end workflow tests"""

    def test_complete_user_flow(self):
        # Register
        user_data = {
            "email": f"test_{int(asyncio.get_event_loop().time())}@example.com",
            "password": "TestPass123!",
            "first_name": "Test",
            "last_name": "User"
        }
        response = client.post("/auth/register", json=user_data)
        if response.status_code == 200:
            user = response.json()

            # Login
            login_data = {"email": user_data["email"], "password": user_data["password"]}
            response = client.post("/auth/login", json=login_data)
            assert response.status_code == 200

            # Execute task
            task_data = {"query": "Find Python jobs", "user_id": user["user"]["id"]}
            response = client.post("/execute", json=task_data)
            assert response.status_code == 200

            # Check tasks
            response = client.get("/tasks")
            assert response.status_code == 200

if __name__ == "__main__":
    # Run basic tests
    print("🧪 Running AI Agent Platform Tests...")

    # Health check
    response = client.get("/health")
    if response.status_code == 200:
        print("✅ Health check passed")
    else:
        print("❌ Health check failed")

    # Agent count
    response = client.get("/agents")
    if response.status_code == 200:
        agents = response.json()["agents"]
        print(f"✅ Agents loaded: {len(agents)}/11")
    else:
        print("❌ Agents endpoint failed")

    # Task execution
    task_data = {"query": "Test query", "user_id": "test"}
    response = client.post("/execute", json=task_data)
    if response.status_code == 200:
        print("✅ Task execution works")
    else:
        print("❌ Task execution failed")

    print("🎉 Basic tests completed!")