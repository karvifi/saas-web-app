#!/bin/bash

echo "🚀 Deploying AI Agent Platform - Complete Version"
echo ""

# Backup current setup
echo "📦 Creating backup..."
cp backend/main.py backend/main.py.backup 2>/dev/null

# Move complete version to production
echo "🔧 Activating complete version..."
cp backend/main_complete.py backend/main.py

# Install any missing dependencies
echo "📥 Installing dependencies..."
pip install -q -r requirements.txt

# Create necessary directories
echo "📁 Setting up directories..."
mkdir -p logs data/user_profiles data/cache data/crawl

# Set permissions
chmod +x deploy.sh

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🎯 Next steps:"
echo "1. Update .env with your Gemini API key"
echo "2. Restart backend: python backend/main.py"
echo "3. Access platform at http://localhost:8000"
echo ""
echo "🌍 You now have the world's most advanced AI platform!"