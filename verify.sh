#!/bin/bash

echo "🔍 Verifying AI Agent Platform Setup..."
echo ""

# Check Python environment
echo "✅ Python version:"
python --version

# Check dependencies
echo ""
echo "✅ Key packages installed:"
pip list | grep -E "fastapi|playwright|langchain|pydantic"

# Check project structure
echo ""
echo "✅ Project structure:"
tree -L 2 -I 'venv|__pycache__|*.pyc|node_modules' ~/ai-agent-platform

# Check environment
echo ""
echo "✅ Environment variables:"
if [ -f .env ]; then
    echo "   .env file exists"
    if grep -q "GOOGLE_API_KEY" .env; then
        echo "   ✅ GOOGLE_API_KEY configured"
    else
        echo "   ❌ GOOGLE_API_KEY not configured"
    fi
else
    echo "   ❌ .env file missing"
fi

# Check if services are running
echo ""
echo "✅ Running services:"
if lsof -i :8000 >/dev/null 2>&1; then
    echo "   ✅ Backend running on port 8000"
else
    echo "   ❌ Backend not running"
fi

if lsof -i :3000 >/dev/null 2>&1; then
    echo "   ✅ Frontend running on port 3000"
else
    echo "   ❌ Frontend not running"
fi

# Check Git status
echo ""
echo "✅ Git status:"
git status --short | head -5

echo ""
echo "🎉 Verification complete!"