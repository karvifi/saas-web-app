"""
Tests for API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


def test_health_check(client):
    """Test health check endpoint"""
    response = client.get("/")
    assert response.status_code == 200


def test_pricing_endpoint(client):
    """Test pricing endpoint"""
    response = client.get("/api/v1/pricing")
    assert response.status_code == 200

    data = response.json()
    assert "pricing" in data
    assert len(data["pricing"]) == 4  # free, starter, professional, enterprise

    # Check structure of each tier
    for tier_name, tier_data in data["pricing"].items():
        assert "price" in tier_data
        assert "monthly_tasks" in tier_data
        assert "description" in tier_data


def test_register_endpoint(client):
    """Test user registration"""
    user_data = {
        "email": "test@example.com",
        "password": "testpass123"
    }

    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code in [200, 400]  # 200 if new user, 400 if exists

    if response.status_code == 200:
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"


def test_execute_endpoint_requires_auth(client):
    """Test execute endpoint requires authentication"""
    task_data = {
        "query": "Find Python jobs"
    }

    response = client.post("/api/v1/execute", json=task_data)
    # Should require subscription (403) for free users
    assert response.status_code == 403


def test_subscription_status(client):
    """Test subscription status endpoint"""
    response = client.get("/api/v1/subscription/test_user")
    assert response.status_code == 200

    data = response.json()
    assert "subscription" in data
    assert "status" in data
    assert data["status"] == "success"