#!/usr/bin/env python3
"""
MINIMAL TEST
"""

import requests
import time

BASE_URL = "http://localhost:8000"

def main():
    print("Testing server...")
    try:
        print("Making GET request to /")
        response = requests.get(BASE_URL, timeout=5)
        print(f"GET /: {response.status_code}")
        print(f"Response content length: {len(response.text)}")
    except Exception as e:
        print(f"GET / Error: {e}")
        return

    # Test register
    try:
        print("Making POST request to /api/v1/auth/register")
        data = {"email": f"test{int(time.time())}@example.com", "password": "pass", "first_name": "Test"}
        response = requests.post(f"{BASE_URL}/api/v1/auth/register", json=data, timeout=10)
        print(f"Register: {response.status_code}")
        print(f"Response: {response.text[:200]}")
    except Exception as e:
        print(f"Register error: {e}")

if __name__ == "__main__":
    main()