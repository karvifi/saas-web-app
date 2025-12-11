Write-Host "============================================" -ForegroundColor Cyan
Write-Host "🤖 AI AGENT PLATFORM v4.0 - PRODUCTION" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Starting complete AI Agent Platform with:" -ForegroundColor Green
Write-Host "• 11 AI Agents (Search, Career, Travel, etc.)" -ForegroundColor Yellow
Write-Host "• SQLite Database with persistent storage" -ForegroundColor Yellow
Write-Host "• JWT Authentication & Security" -ForegroundColor Yellow
Write-Host "• Rate Limiting & Input Validation" -ForegroundColor Yellow
Write-Host "• Comprehensive Testing Suite" -ForegroundColor Yellow
Write-Host ""
Set-Location "d:\nexus browser\try - Copy\ai-agent-platform"
python production_backend.py
Read-Host "Press Enter to exit"