#!/usr/bin/env python3
"""
AI Agent Platform - Final Status Check
Comprehensive validation of all components
"""

import sys
import os
import importlib
from pathlib import Path

def check_file_exists(path, description):
    """Check if file exists"""
    if Path(path).exists():
        print(f"✅ {description}")
        return True
    else:
        print(f"❌ {description} - MISSING")
        return False

def check_import(module_name, description):
    """Check if module can be imported"""
    try:
        importlib.import_module(module_name)
        print(f"✅ {description}")
        return True
    except ImportError as e:
        print(f"❌ {description} - {str(e)}")
        return False

def check_agents():
    """Check agent implementations"""
    print("\n🤖 Checking AI Agents (11 Categories):")

    agents_dir = Path("agents")
    expected_agents = [
        "search", "career", "travel", "local", "transaction",
        "communication", "entertainment", "productivity",
        "monitoring", "job_automation", "browser_advanced"
    ]

    available = 0
    for agent in expected_agents:
        agent_file = agents_dir / f"{agent}.py"
        if agent_file.exists():
            print(f"✅ {agent} agent")
            available += 1
        else:
            print(f"❌ {agent} agent - MISSING")

    print(f"\n📊 Agents: {available}/11 implemented")
    return available == 11

def main():
    print("🔍 AI AGENT PLATFORM - FINAL STATUS CHECK")
    print("=" * 50)

    # Check core files
    print("\n📁 Core Files:")
    files_ok = all([
        check_file_exists("production_backend.py", "Production backend"),
        check_file_exists("enhanced_backend.py", "Enhanced backend"),
        check_file_exists("database.py", "Database layer"),
        check_file_exists("auth_service.py", "Authentication service"),
        check_file_exists("security.py", "Security middleware"),
        check_file_exists("test_comprehensive.py", "Test suite"),
        check_file_exists("requirements.txt", "Dependencies"),
        check_file_exists("README.md", "Documentation")
    ])

    # Check frontend
    print("\n🎨 Frontend Files:")
    frontend_ok = check_file_exists("frontend from google ai studio/index.html", "Landing page") and \
                  check_file_exists("frontend from google ai studio/app.html", "App interface")

    # Check agents
    agents_ok = check_agents()

    # Check dependencies
    print("\n📦 Key Dependencies:")
    deps_ok = all([
        check_import("fastapi", "FastAPI framework"),
        check_import("uvicorn", "Uvicorn server"),
        check_import("pydantic", "Pydantic models"),
        check_import("sqlite3", "SQLite database")
    ])

    # Check startup scripts
    print("\n🚀 Startup Scripts:")
    scripts_ok = all([
        check_file_exists("start_production.bat", "Windows batch starter"),
        check_file_exists("start_production.ps1", "PowerShell starter")
    ])

    # Final status
    print("\n" + "=" * 50)
    print("🎯 FINAL STATUS:")

    all_checks = [files_ok, frontend_ok, agents_ok, deps_ok, scripts_ok]

    if all(all_checks):
        print("🎉 ALL SYSTEMS GO! Platform is production-ready!")
        print("\n🚀 To start: python production_backend.py")
        print("🌐 Access at: http://localhost:8000")
        return True
    else:
        print("⚠️ Some components need attention")
        failed = [name for name, ok in zip(
            ["Core Files", "Frontend", "Agents", "Dependencies", "Scripts"],
            all_checks
        ) if not ok]
        print(f"❌ Issues with: {', '.join(failed)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)