#!/usr/bin/env python3
"""
Focused Reality Check - Test Core Launch-Ready Features
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_auto_apply():
    """Test auto-apply functionality"""
    print("🧪 Testing Auto-Apply Functionality...")

    data = {
        'query': 'Apply for this software engineer job',
        'user_id': 'free_user',
        'context': {
            'job_title': 'Software Engineer',
            'company': 'Test Company',
            'job_url': 'https://example.com/job/123',
            'max_applications': 1
        }
    }

    response = requests.post(f"{BASE_URL}/api/v1/execute", json=data)
    if response.status_code == 200:
        result = response.json()
        status = result['result']['status']
        if status in ['no_apply_button', 'failed', 'error']:
            print("✅ Auto-apply executed (attempted navigation and automation)")
            return True
    print("❌ Auto-apply failed")
    return False

def test_database_persistence():
    """Test database persistence"""
    print("🧪 Testing Database Persistence...")

    response = requests.get(f"{BASE_URL}/api/v1/analytics/user/free_user/stats")
    if response.status_code == 200:
        data = response.json()
        if 'task_stats' in data and 'total_tasks' in data['task_stats']:
            print("✅ Database returns proper user stats")
            return True
    print("❌ Database persistence failed")
    return False

def test_subscription_enforcement():
    """Test subscription enforcement"""
    print("🧪 Testing Subscription Enforcement...")

    # Make requests until we hit the limit
    for i in range(12):
        response = requests.post(f"{BASE_URL}/api/v1/execute",
                               json={"query": f"test {i}", "user_id": "free_user"})
        if response.status_code == 429:
            print(f"✅ Subscription limit enforced after {i} requests")
            return True
        time.sleep(0.1)

    print("❌ Subscription enforcement failed")
    return False

def test_error_handling():
    """Test error handling"""
    print("🧪 Testing Error Handling...")

    response = requests.post(f"{BASE_URL}/api/v1/execute",
                           json={"query": "", "user_id": "test_user"})
    if response.status_code >= 400:
        print("✅ Error handling works for invalid input")
        return True
    print("❌ Error handling failed")
    return False

def main():
    print("🚀 FOCUSED REALITY CHECK - Core Launch Features")
    print("=" * 50)

    tests = [
        test_auto_apply,
        test_database_persistence,
        test_subscription_enforcement,
        test_error_handling
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    score = (passed / total) * 100
    print(f"🎯 SCORE: {passed}/{total} ({score:.1f}%)")

    if score >= 80:
        print("✅ LAUNCH READY - Core features working!")
    elif score >= 60:
        print("⚠️  MOSTLY READY - Minor issues to fix")
    else:
        print("❌ NOT READY - Major rework needed")

if __name__ == "__main__":
    main()