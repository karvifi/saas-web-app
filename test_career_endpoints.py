import asyncio
import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.career import career_agent

async def test_career_endpoints():
    print(" Testing Career Agent Endpoints\n")
    
    # Test 1: Job Search
    print("1 Testing Job Search...")
    try:
        results = await career_agent.execute(
            query="Python developer",
            action="search",
            location="remote",
            job_type="remote"
        )
        count = results.get("count", 0)
        print(f" Search successful: Found {count} jobs")
        if results.get("jobs"):
            title = results["jobs"][0].get("title", "N/A")
            print(f"Sample job: {title}")
    except Exception as e:
        print(f" Search failed: {e}")
    
    # Test 2: Job Apply (mock)
    print("\n2 Testing Job Apply (mock)...")
    try:
        result = await career_agent.execute(
            query="",
            action="apply",
            job_url="https://example.com/job/123",
            resume="Test resume content",
            email="test@example.com",
            phone="+1234567890",
            name="Test User"
        )
        status = result.get("status", "unknown")
        print(f" Apply result: {status}")
    except Exception as e:
        print(f" Apply failed: {e}")
    
    print("\n Career endpoint tests completed!")

if __name__ == "__main__":
    asyncio.run(test_career_endpoints())
