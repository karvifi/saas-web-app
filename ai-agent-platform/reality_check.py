#!/usr/bin/env python3
"""
🔍 AI AGENT PLATFORM - REALITY CHECK SCRIPT
Tests what ACTUALLY works vs what the blueprint claims
"""

import asyncio
import requests
import json
import time
from datetime import datetime
import sys
import os

# Add backend to path
sys.path.insert(0, 'backend')

class RealityCheck:
    """Brutally honest testing of what actually works"""

    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.results = {
            "career_agent": {},
            "database": {},
            "authentication": {},
            "subscription_enforcement": {},
            "error_handling": {},
            "integrations": {},
            "overall_score": 0
        }

    def log(self, message, status="INFO"):
        """Log with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {status}: {message}")

    async def test_career_agent_reality(self):
        """Test if career agent actually applies to jobs"""
        self.log("🧪 TESTING CAREER AGENT REALITY", "START")

        # Test 1: Basic job search via execute endpoint
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/execute",
                json={"query": "Find Python developer jobs in Berlin", "user_id": "test_user"},
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                self.results["career_agent"]["basic_search"] = True
                self.log("✅ Basic job search works")
                if "result" in data and "jobs" in data["result"]:
                    job_count = len(data["result"]["jobs"])
                    self.log(f"✅ Found {job_count} jobs")
                else:
                    self.log("❌ No jobs found in response")
                    self.results["career_agent"]["basic_search"] = False
            else:
                self.log(f"❌ Basic search failed: {response.status_code}")
                self.results["career_agent"]["basic_search"] = False

        except Exception as e:
            self.log(f"❌ Basic search error: {e}")
            self.results["career_agent"]["basic_search"] = False

        # Test 2: Auto-apply attempt (this is the critical test)
        try:
            self.log("🧪 TESTING AUTO-APPLY FUNCTIONALITY (REVENUE DRIVER)")

            # Try to auto-apply using the execute endpoint
            response = requests.post(
                f"{self.base_url}/api/v1/execute",
                json={
                    "query": "Apply to Python developer jobs automatically",
                    "user_id": "test_user",
                    "context": {
                        "job_title": "Python Developer",
                        "company": "Test Company",
                        "job_url": "https://remoteok.com/remote-jobs/python-developer-at-test-company"
                    }
                },
                timeout=60
            )

            if response.status_code == 200:
                data = response.json()
                result = data.get("result", {})
                self.log(f"Auto-apply response: {result}")  # Debug logging

                # Check if it actually tried to apply
                if "applied" in str(result).lower() or "application" in str(result).lower():
                    self.results["career_agent"]["auto_apply_attempt"] = True
                    self.log("✅ Auto-apply was attempted")
                else:
                    self.results["career_agent"]["auto_apply_attempt"] = False
                    self.log("❌ Auto-apply was NOT attempted - just returned search results")
            else:
                self.log(f"❌ Auto-apply request failed: {response.status_code}")
                self.results["career_agent"]["auto_apply_attempt"] = False

        except Exception as e:
            self.log(f"❌ Auto-apply test error: {e}")
            self.results["career_agent"]["auto_apply_attempt"] = False

    def test_database_reality(self):
        """Test if database actually persists data"""
        self.log("🧪 TESTING DATABASE REALITY", "START")

        # Test 1: Check if user stats endpoint works (indicates database integration)
        try:
            response = requests.get(f"{self.base_url}/api/v1/analytics/user/test_user/stats")

            if response.status_code == 200:
                data = response.json()
                self.results["database"]["stats_endpoint"] = True
                self.log("✅ User stats endpoint works")

                # Check if it has the expected structure
                if "task_stats" in data and "job_stats" in data:
                    self.results["database"]["stats_structure"] = True
                    self.log("✅ Database returns proper stats structure")
                else:
                    self.results["database"]["stats_structure"] = False
                    self.log("❌ Database stats structure incorrect")
            else:
                self.results["database"]["stats_endpoint"] = False
                self.log(f"❌ User stats endpoint failed: {response.status_code}")

        except Exception as e:
            self.log(f"❌ Database test error: {e}")
            self.results["database"]["stats_endpoint"] = False
            self.results["database"]["stats_structure"] = False

    def test_authentication_reality(self):
        """Test if authentication actually secures endpoints"""
        self.log("🧪 TESTING AUTHENTICATION REALITY", "START")

        # Test 1: Can anyone call execute without auth?
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/execute",
                json={"query": "test", "user_id": "hacker_user"}
            )

            if response.status_code == 200:
                self.results["authentication"]["no_auth_required"] = True
                self.log("❌ NO AUTHENTICATION - Anyone can call endpoints")
            elif response.status_code == 401:
                self.results["authentication"]["no_auth_required"] = False
                self.log("✅ Authentication required")
            else:
                self.log(f"⚠️ Unexpected auth response: {response.status_code}")

        except Exception as e:
            self.log(f"❌ Auth test error: {e}")

    def test_subscription_enforcement_reality(self):
        """Test if subscription limits are actually enforced"""
        self.log("🧪 TESTING SUBSCRIPTION ENFORCEMENT REALITY", "START")

        # Test 1: Can free user make unlimited requests?
        try:
            # Make multiple requests as "free" user
            success_count = 0
            for i in range(5):
                response = requests.post(
                    f"{self.base_url}/api/v1/execute",
                    json={"query": f"test query {i}", "user_id": "free_user"}
                )
                if response.status_code == 200:
                    success_count += 1
                time.sleep(0.1)  # Small delay

            if success_count >= 5:
                self.results["subscription_enforcement"]["no_limits"] = True
                self.log("❌ NO SUBSCRIPTION ENFORCEMENT - Free user can make unlimited requests")
            else:
                self.results["subscription_enforcement"]["no_limits"] = False
                self.log("✅ Subscription limits enforced")

        except Exception as e:
            self.log(f"❌ Subscription test error: {e}")

    def test_error_handling_reality(self):
        """Test error handling when things go wrong"""
        self.log("🧪 TESTING ERROR HANDLING REALITY", "START")

        # Test 1: Invalid query
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/execute",
                json={"query": "", "user_id": "test_user"}
            )

            if response.status_code >= 400:
                data = response.json()
                if "error" in data or "detail" in data:
                    self.results["error_handling"]["graceful_errors"] = True
                    self.log("✅ Errors handled gracefully")
                else:
                    self.results["error_handling"]["graceful_errors"] = False
                    self.log("❌ Error response lacks user-friendly message")
            else:
                self.results["error_handling"]["graceful_errors"] = False
                self.log("❌ Invalid input not rejected")

        except Exception as e:
            self.log(f"❌ Error handling test error: {e}")

    def test_integrations_reality(self):
        """Test if claimed integrations actually work"""
        self.log("🧪 TESTING INTEGRATIONS REALITY", "START")

        integrations_to_test = [
            ("RemoteOK API", "Find remote Python jobs"),
            ("Travel planning", "Plan a trip from Berlin to Munich"),
            ("Shopping", "Find cheap laptops"),
            ("Entertainment", "Find action movies"),
        ]

        for name, query in integrations_to_test:
            try:
                response = requests.post(
                    f"{self.base_url}/api/v1/execute",
                    json={"query": query, "user_id": "test_user"},
                    timeout=30
                )

                if response.status_code == 200:
                    data = response.json()
                    result = data.get("result", {})

                    # Check if it returned actual data vs generic search
                    if isinstance(result, dict) and len(result) > 0:
                        self.results["integrations"][name.lower().replace(" ", "_")] = True
                        self.log(f"✅ {name} integration works")
                    else:
                        self.results["integrations"][name.lower().replace(" ", "_")] = False
                        self.log(f"❌ {name} integration returns empty/generic results")
                else:
                    self.results["integrations"][name.lower().replace(" ", "_")] = False
                    self.log(f"❌ {name} integration failed: {response.status_code}")

            except Exception as e:
                self.log(f"❌ {name} integration error: {e}")
                self.results["integrations"][name.lower().replace(" ", "_")] = False

    def calculate_overall_score(self):
        """Calculate what percentage actually works"""
        scores = []

        # Career agent (most important - 30% weight)
        career_score = 0
        if self.results["career_agent"].get("basic_search"):
            career_score += 50
        if self.results["career_agent"].get("auto_apply_attempt"):
            career_score += 50  # Critical for revenue
        scores.append(("Career Agent", career_score, 30))

        # Database (20% weight)
        db_score = 100 if self.results["database"].get("profile_persistence") else 0
        scores.append(("Database", db_score, 20))

        # Authentication (15% weight)
        auth_score = 0 if self.results["authentication"].get("no_auth_required") else 100
        scores.append(("Authentication", auth_score, 15))

        # Subscription enforcement (15% weight)
        sub_score = 0 if self.results["subscription_enforcement"].get("no_limits") else 100
        scores.append(("Subscription Enforcement", sub_score, 15))

        # Error handling (10% weight)
        error_score = 100 if self.results["error_handling"].get("graceful_errors") else 0
        scores.append(("Error Handling", error_score, 10))

        # Integrations (10% weight)
        integration_count = sum(1 for v in self.results["integrations"].values() if v)
        integration_score = (integration_count / len(self.results["integrations"])) * 100
        scores.append(("Integrations", integration_score, 10))

        # Calculate weighted average
        total_score = sum(score * weight / 100 for _, score, weight in scores)

        self.results["overall_score"] = round(total_score, 1)

        self.log("\n📊 REALITY CHECK RESULTS", "FINAL")
        self.log("=" * 50, "FINAL")
        for name, score, weight in scores:
            self.log(f"{name}: {score}% (weight: {weight}%)", "FINAL")

        self.log(f"\n🎯 OVERALL SCORE: {self.results['overall_score']}%", "FINAL")

        if self.results["overall_score"] >= 90:
            self.log("✅ READY FOR LAUNCH", "FINAL")
        elif self.results["overall_score"] >= 70:
            self.log("⚠️ LAUNCH WITH CAUTION - Fix critical issues", "FINAL")
        else:
            self.log("❌ NOT READY - Major rework needed", "FINAL")

        return self.results

    async def run_all_tests(self):
        """Run all reality checks"""
        self.log("🚀 STARTING AI AGENT PLATFORM REALITY CHECK", "START")
        self.log("This will test what ACTUALLY works vs blueprint claims", "START")

        # Check if server is running
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            if response.status_code != 200:
                self.log(f"❌ Server not responding: {response.status_code}")
                return None
        except:
            self.log("❌ Cannot connect to server. Start with: python backend/main.py")
            return None

        self.log("✅ Server is running")

        # Run all tests
        await self.test_career_agent_reality()
        self.test_database_reality()
        self.test_authentication_reality()
        self.test_subscription_enforcement_reality()
        self.test_error_handling_reality()
        self.test_integrations_reality()

        return self.calculate_overall_score()

async def main():
    """Main test runner"""
    checker = RealityCheck()

    results = await checker.run_all_tests()

    if results:
        # Save results
        with open("reality_check_results.json", "w") as f:
            json.dump(results, f, indent=2)

        print(f"\n📄 Results saved to: reality_check_results.json")

        # Give recommendations
        score = results["overall_score"]

        print("\n🎯 RECOMMENDATIONS:")
        if score >= 90:
            print("✅ LAUNCH NOW - Everything works!")
        elif score >= 70:
            print("⚠️  FIX CRITICAL ISSUES THEN LAUNCH:")
            if not results["career_agent"].get("auto_apply_attempt"):
                print("   - Career agent auto-apply doesn't work (fix revenue driver)")
            if results["authentication"].get("no_auth_required"):
                print("   - No authentication (security risk)")
            if results["subscription_enforcement"].get("no_limits"):
                print("   - No subscription enforcement (revenue leak)")
        else:
            print("❌ DO NOT LAUNCH - Major issues:")
            issues = []
            if not results["database"].get("profile_persistence"):
                issues.append("No database persistence")
            if results["authentication"].get("no_auth_required"):
                issues.append("No security")
            if results["subscription_enforcement"].get("no_limits"):
                issues.append("No subscription limits")
            if not results["error_handling"].get("graceful_errors"):
                issues.append("Poor error handling")

            for issue in issues:
                print(f"   - {issue}")

if __name__ == "__main__":
    asyncio.run(main())