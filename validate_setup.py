#!/usr/bin/env python3
"""
Validation script for AI Agent Platform
Checks if all dependencies are installed and system is ready
"""

import sys
import importlib

def check_dependency(name: str, package: str = None):
    """Check if a dependency is available"""
    try:
        if package:
            importlib.import_module(package)
        else:
            importlib.import_module(name)
        print(f"✅ {name}")
        return True
    except ImportError:
        print(f"❌ {name} - NOT INSTALLED")
        return False

def main():
    print("🔍 Validating AI Agent Platform Dependencies...\n")

    required_deps = [
        ("fastapi", "fastapi"),
        ("uvicorn", "uvicorn"),
        ("pydantic", "pydantic"),
        ("requests", "requests"),
        ("pathlib", "pathlib"),
        ("asyncio", None),  # Built-in
        ("json", None),     # Built-in
        ("datetime", None), # Built-in
    ]

    optional_deps = [
        ("stripe", "stripe"),
        ("httpx", "httpx"),
        ("playwright", "playwright"),
    ]

    print("📦 Required Dependencies:")
    all_required = True
    for name, package in required_deps:
        if not check_dependency(name, package):
            all_required = False

    print("\n📦 Optional Dependencies:")
    for name, package in optional_deps:
        check_dependency(name, package)

    print("\n" + "="*50)

    if all_required:
        print("🎉 All required dependencies are installed!")
        print("🚀 Ready to run: python complete_backend.py")
    else:
        print("❌ Missing required dependencies.")
        print("📥 Install with: pip install -r requirements.txt")

    return all_required

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)