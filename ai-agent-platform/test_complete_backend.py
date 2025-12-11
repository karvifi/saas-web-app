#!/usr/bin/env python3
"""
Test script for the complete backend
"""

import requests
import time
import json

def test_backend():
    print("🧪 Testing AI Agent Platform Backend...")

    # Test health endpoint
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Status: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

    # Test agents endpoint
    try:
        response = requests.get("http://localhost:8000/agents")
        if response.status_code == 200:
            print("✅ Agents endpoint passed")
            agents = response.json()["agents"]
            print(f"   Available agents: {len(agents)}")
        else:
            print(f"❌ Agents endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Agents endpoint error: {e}")

    # Test task execution
    try:
        task_data = {
            "query": "Find Python developer jobs in Berlin",
            "user_id": "test_user"
        }
        response = requests.post("http://localhost:8000/execute", json=task_data)
        if response.status_code == 200:
            print("✅ Task execution passed")
            result = response.json()
            print(f"   Task ID: {result['task_id']}")
            print(f"   Agent: {result['agent']}")
            print(f"   Status: {result['status']}")
        else:
            print(f"❌ Task execution failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Task execution error: {e}")

    # Test root endpoint
    try:
        response = requests.get("http://localhost:8000/")
        if response.status_code == 200:
            print("✅ Root endpoint passed")
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Root endpoint error: {e}")

    print("🎉 Backend testing complete!")
    return True

if __name__ == "__main__":
    test_backend()