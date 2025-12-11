#!/bin/bash

# AI Agent Platform Production Deployment Script
# Run this on your cloud server (Railway/Render/Vercel)

echo "🚀 Deploying AI Agent Platform to Production"
echo ""

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Set environment variables (replace with your actual keys)
echo "🔑 Setting environment variables..."
export STRIPE_SECRET_KEY="${STRIPE_SECRET_KEY:-sk_test_your_stripe_secret_key}"
export STRIPE_PUBLISHABLE_KEY="${STRIPE_PUBLISHABLE_KEY:-pk_test_your_stripe_publishable_key}"
export GOOGLE_API_KEY="${GOOGLE_API_KEY:-your_google_api_key}"
export BACKEND_PORT="${PORT:-8000}"

# Create necessary directories
echo "📁 Setting up directories..."
mkdir -p logs data/user_profiles data/cache data/crawl

# Run database migrations if needed
echo "🗄️ Setting up database..."
python -c "from backend.user_profiles import UserProfiles; UserProfiles()"

echo ""
echo "✅ Production deployment complete!"
echo ""
echo "🎯 Your AI Agent Platform is now live!"
echo "🌍 Access it at your cloud URL"
echo ""

# Run the application
echo "🚀 Starting server..."
uvicorn backend.main:app --host 0.0.0.0 --port $BACKEND_PORT