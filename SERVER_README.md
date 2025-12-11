# AI Agent Platform

A comprehensive AI agent platform built with FastAPI.

## Quick Start

1. Install dependencies:
   pip install -r requirements.txt

2. Start the server:
   python server.py

   Or use the PowerShell script:
   .\start.ps1

3. The server will be available at:
   - API: http://localhost:8000
   - Health check: http://localhost:8000/health
   - Stats: http://localhost:8000/stats

## Features

- 11 specialized AI agents
- Advanced orchestrator for agent coordination
- RESTful API endpoints
- Static file serving for frontend
- Comprehensive error handling

## API Endpoints

- GET / - Main page
- GET /health - Health check
- GET /stats - Server statistics
- POST /execute - Execute agent queries
- GET /app - App page
- POST /subscribe - Subscription management
- POST /webhook/stripe - Stripe webhooks

## Agents Available

- Search Agent
- Career Agent
- Travel Agent
- Local Agent
- Transaction Agent
- Communication Agent
- Entertainment Agent
- Productivity Agent
- Monitoring Agent
- Browser Automation Agent
- Common Crawl Agent

## Development

The server includes hot reload and will automatically restart when code changes are detected.
