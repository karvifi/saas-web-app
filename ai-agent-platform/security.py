"""
Security and rate limiting for AI Agent Platform
"""

import time
from collections import defaultdict
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import re

class RateLimiter:
    """Simple in-memory rate limiter"""

    def __init__(self):
        self.requests = defaultdict(list)
        self.limits = {
            "free": {"requests_per_minute": 10, "requests_per_hour": 50},
            "starter": {"requests_per_minute": 100, "requests_per_hour": 1000},
            "professional": {"requests_per_minute": 1000, "requests_per_hour": 10000},
            "enterprise": {"requests_per_minute": 10000, "requests_per_hour": 100000}
        }

    def is_allowed(self, user_id: str, tier: str = "free") -> bool:
        """Check if request is allowed under rate limits"""
        now = time.time()
        user_requests = self.requests[user_id]

        # Clean old requests (older than 1 hour)
        user_requests[:] = [req for req in user_requests if now - req < 3600]

        limits = self.limits.get(tier, self.limits["free"])

        # Check minute limit
        recent_requests = [req for req in user_requests if now - req < 60]
        if len(recent_requests) >= limits["requests_per_minute"]:
            return False

        # Check hour limit
        if len(user_requests) >= limits["requests_per_hour"]:
            return False

        # Add current request
        user_requests.append(now)
        return True

class SecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware for input validation and protection"""

    def __init__(self, app, rate_limiter: RateLimiter = None):
        super().__init__(app)
        self.rate_limiter = rate_limiter or RateLimiter()
        self.suspicious_patterns = [
            r'<script[^>]*>.*?</script>',  # XSS attempts
            r'union.*select.*--',  # SQL injection
            r'../../../',  # Path traversal
            r'eval\(',  # Code injection
            r'exec\(',  # Code execution
        ]

    async def dispatch(self, request: Request, call_next):
        # Get client info
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "")

        # Basic security checks
        if self._is_suspicious_request(request):
            return JSONResponse(
                status_code=403,
                content={"error": "Suspicious request detected"}
            )

        # Rate limiting (skip for health checks)
        if request.url.path not in ["/health", "/"]:
            # For now, use IP-based limiting since we don't have user context yet
            if not self.rate_limiter.is_allowed(client_ip, "free"):
                return JSONResponse(
                    status_code=429,
                    content={"error": "Rate limit exceeded. Please try again later."}
                )

        # Add security headers to response
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"

        return response

    def _is_suspicious_request(self, request: Request) -> bool:
        """Check for suspicious patterns in request"""
        # Check query parameters
        for param in request.query_params.values():
            if self._contains_suspicious_pattern(str(param)):
                return True

        # Check headers
        for header_value in request.headers.values():
            if self._contains_suspicious_pattern(str(header_value)):
                return True

        return False

    def _contains_suspicious_pattern(self, text: str) -> bool:
        """Check if text contains suspicious patterns"""
        text_lower = text.lower()
        for pattern in self.suspicious_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True
        return False

class InputValidator:
    """Input validation utilities"""

    @staticmethod
    def sanitize_query(query: str) -> str:
        """Sanitize user query input"""
        if not query or len(query.strip()) == 0:
            raise ValueError("Query cannot be empty")

        if len(query) > 1000:
            raise ValueError("Query too long (max 1000 characters)")

        # Basic sanitization
        query = query.strip()

        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '"', "'", ';', '--', '/*', '*/']
        for char in dangerous_chars:
            query = query.replace(char, '')

        return query

    @staticmethod
    def validate_email(email: str) -> bool:
        """Basic email validation"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    @staticmethod
    def validate_password(password: str) -> bool:
        """Password strength validation"""
        if len(password) < 8:
            return False
        if not any(c.isupper() for c in password):
            return False
        if not any(c.islower() for c in password):
            return False
        if not any(c.isdigit() for c in password):
            return False
        return True

# Global instances
rate_limiter = RateLimiter()
input_validator = InputValidator()