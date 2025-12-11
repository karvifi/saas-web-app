"""
API versioning and advanced rate limiting for AI Agent Platform
Version management, endpoint versioning, and sophisticated rate limiting
"""

from fastapi import Request, HTTPException, APIRouter, Depends
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict, List, Any, Optional, Callable
import time
import asyncio
from datetime import datetime, timedelta
import logging
import re
from collections import defaultdict
import hashlib
import json

logger = logging.getLogger(__name__)

class APIVersionManager:
    """Manages API versioning and routing"""

    def __init__(self):
        self.versions: Dict[str, Dict[str, Any]] = {}
        self.current_version = "v1"
        self.supported_versions = ["v1"]

    def register_version(self, version: str, router: APIRouter, deprecated: bool = False):
        """Register an API version"""
        self.versions[version] = {
            "router": router,
            "deprecated": deprecated,
            "endpoints": []
        }

        if version not in self.supported_versions:
            self.supported_versions.append(version)

        logger.info(f"Registered API version: {version}")

    def get_version_info(self) -> Dict[str, Any]:
        """Get information about all versions"""
        return {
            "current_version": self.current_version,
            "supported_versions": self.supported_versions,
            "versions": {
                v: {
                    "deprecated": info["deprecated"],
                    "endpoint_count": len(info["endpoints"])
                }
                for v, info in self.versions.items()
            }
        }

    def set_current_version(self, version: str):
        """Set the current API version"""
        if version not in self.versions:
            raise ValueError(f"Version {version} not registered")
        self.current_version = version
        logger.info(f"Current API version set to: {version}")

class AdvancedRateLimiter:
    """Advanced rate limiting with multiple strategies"""

    def __init__(self):
        self.rules: Dict[str, Dict[str, Any]] = {}
        self.request_history: Dict[str, List[float]] = defaultdict(list)

    def add_rule(self, name: str, limits: Dict[str, Any]):
        """Add a rate limiting rule"""
        self.rules[name] = {
            "requests_per_minute": limits.get("rpm", 60),
            "requests_per_hour": limits.get("rph", 1000),
            "burst_limit": limits.get("burst", 10),
            "cooldown_seconds": limits.get("cooldown", 60),
            "backoff_multiplier": limits.get("backoff", 2.0),
            "user_specific": limits.get("user_specific", True),
            "endpoint_specific": limits.get("endpoint_specific", False)
        }

        logger.info(f"Added rate limit rule: {name}")

    def get_rule_for_endpoint(self, endpoint: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get applicable rate limit rule for an endpoint"""
        # Check for endpoint-specific rules first
        for rule_name, rule in self.rules.items():
            if rule.get("endpoint_specific") and rule_name in endpoint:
                return rule

        # Check for user-specific rules
        if user_id:
            user_rule = f"user_{user_id}"
            if user_rule in self.rules:
                return self.rules[user_rule]

        # Default rules based on endpoint type
        if "/admin/" in endpoint:
            return self.rules.get("admin", self.rules.get("default"))
        elif "/agent/" in endpoint:
            return self.rules.get("agent", self.rules.get("default"))
        else:
            return self.rules.get("default")

    async def check_rate_limit(self, request: Request, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Check if request should be rate limited"""
        endpoint = request.url.path
        method = request.method

        # Get applicable rule
        rule = self.get_rule_for_endpoint(endpoint, user_id)
        if not rule:
            return {"allowed": True, "rule": "none"}

        # Create identifier for rate limiting
        if rule.get("user_specific") and user_id:
            identifier = f"user:{user_id}:{endpoint}"
        else:
            # Use IP-based limiting as fallback
            client_ip = request.client.host if request.client else "unknown"
            identifier = f"ip:{client_ip}:{endpoint}"

        current_time = time.time()
        history = self.request_history[identifier]

        # Clean old requests (older than 1 hour)
        cutoff_time = current_time - 3600
        history[:] = [t for t in history if t > cutoff_time]

        # Check minute limit
        minute_requests = sum(1 for t in history if current_time - t < 60)
        if minute_requests >= rule["requests_per_minute"]:
            return {
                "allowed": False,
                "reason": "minute_limit_exceeded",
                "retry_after": 60,
                "rule": rule
            }

        # Check hour limit
        hour_requests = len(history)
        if hour_requests >= rule["requests_per_hour"]:
            return {
                "allowed": False,
                "reason": "hour_limit_exceeded",
                "retry_after": 3600,
                "rule": rule
            }

        # Check burst limit (requests in last 10 seconds)
        burst_requests = sum(1 for t in history if current_time - t < 10)
        if burst_requests >= rule["burst_limit"]:
            return {
                "allowed": False,
                "reason": "burst_limit_exceeded",
                "retry_after": rule["cooldown_seconds"],
                "rule": rule
            }

        # Add current request to history
        history.append(current_time)

        return {
            "allowed": True,
            "remaining_minute": rule["requests_per_minute"] - minute_requests - 1,
            "remaining_hour": rule["requests_per_hour"] - hour_requests - 1,
            "rule": rule
        }

    def get_rate_limit_headers(self, check_result: Dict[str, Any]) -> Dict[str, str]:
        """Generate rate limit headers for response"""
        headers = {}

        if check_result["allowed"]:
            rule = check_result.get("rule", {})
            headers.update({
                "X-RateLimit-Limit-Minute": str(rule.get("requests_per_minute", 60)),
                "X-RateLimit-Remaining-Minute": str(check_result.get("remaining_minute", 0)),
                "X-RateLimit-Limit-Hour": str(rule.get("requests_per_hour", 1000)),
                "X-RateLimit-Remaining-Hour": str(check_result.get("remaining_hour", 0)),
            })
        else:
            headers["Retry-After"] = str(check_result.get("retry_after", 60))

        return headers

# Global instances
api_version_manager = APIVersionManager()
rate_limiter = AdvancedRateLimiter()

# Default rate limiting rules
rate_limiter.add_rule("default", {
    "rpm": 60,      # 60 requests per minute
    "rph": 1000,    # 1000 requests per hour
    "burst": 10,    # Max 10 requests in 10 seconds
    "cooldown": 60
})

rate_limiter.add_rule("agent", {
    "rpm": 30,      # Agents are more resource intensive
    "rph": 500,
    "burst": 5,
    "cooldown": 120
})

rate_limiter.add_rule("admin", {
    "rpm": 120,     # Admin endpoints can handle more load
    "rph": 2000,
    "burst": 20,
    "cooldown": 30
})

rate_limiter.add_rule("public", {
    "rpm": 20,      # Public endpoints are more restrictive
    "rph": 200,
    "burst": 3,
    "cooldown": 300
})

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting"""

    def __init__(self, app, exclude_paths: List[str] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or ["/docs", "/redoc", "/openapi.json", "/health"]

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for excluded paths
        if any(path in request.url.path for path in self.exclude_paths):
            return await call_next(request)

        # Extract user ID from request (this would come from auth middleware)
        user_id = getattr(request.state, "user_id", None)

        # Check rate limit
        check_result = await rate_limiter.check_rate_limit(request, user_id)

        if not check_result["allowed"]:
            # Rate limit exceeded
            headers = rate_limiter.get_rate_limit_headers(check_result)
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "reason": check_result["reason"],
                    "retry_after": check_result["retry_after"]
                },
                headers=headers
            )

        # Add rate limit headers to response
        response = await call_next(request)
        headers = rate_limiter.get_rate_limit_headers(check_result)

        for header_name, header_value in headers.items():
            response.headers[header_name] = header_value

        return response

class VersioningMiddleware(BaseHTTPMiddleware):
    """Middleware for API versioning"""

    async def dispatch(self, request: Request, call_next):
        # Extract version from Accept header or URL
        version = None

        # Check Accept header (e.g., "application/vnd.aiagent.v1+json")
        accept = request.headers.get("Accept", "")
        version_match = re.search(r'application/vnd\.aiagent\.(\w+)\+json', accept)
        if version_match:
            version = version_match.group(1)

        # Check URL path (e.g., "/v1/endpoint")
        path_match = re.match(r'/v(\d+)/', request.url.path)
        if path_match:
            version = f"v{path_match.group(1)}"

        # Set version on request state
        if version and version in api_version_manager.supported_versions:
            request.state.api_version = version
        else:
            request.state.api_version = api_version_manager.current_version

        # Add version header to response
        response = await call_next(request)
        response.headers["X-API-Version"] = request.state.api_version

        return response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware for security headers"""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Add security headers
        response.headers.update({
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
        })

        return response

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for detailed request logging"""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Log request
        logger.info(f"Request: {request.method} {request.url.path} from {request.client.host if request.client else 'unknown'}")

        try:
            response = await call_next(request)

            # Log response
            duration = time.time() - start_time
            logger.info(f"Response: {response.status_code} for {request.method} {request.url.path} in {duration:.3f}s")

            return response

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Request error: {request.method} {request.url.path} failed after {duration:.3f}s: {e}")
            raise e

# API Version routers
v1_router = APIRouter(prefix="/v1")
v2_router = APIRouter(prefix="/v2")  # Future version

# Register versions
api_version_manager.register_version("v1", v1_router)
api_version_manager.register_version("v2", v2_router, deprecated=False)  # Not deprecated yet

# Version-specific endpoints
@v1_router.get("/version")
async def get_v1_version():
    """Get API version info for v1"""
    return {
        "version": "v1",
        "features": ["basic_agents", "task_execution", "user_management"],
        "deprecated": False
    }

@v2_router.get("/version")
async def get_v2_version():
    """Get API version info for v2"""
    return {
        "version": "v2",
        "features": ["basic_agents", "task_execution", "user_management", "real_time_updates", "advanced_analytics"],
        "deprecated": False
    }

# Global API info endpoint
@v1_router.get("/info")
async def get_api_info():
    """Get comprehensive API information"""
    return {
        "name": "AI Agent Platform API",
        "version": api_version_manager.current_version,
        "versions": api_version_manager.get_version_info(),
        "rate_limits": {
            rule_name: {k: v for k, v in rule.items() if k != "backoff_multiplier"}
            for rule_name, rule in rate_limiter.rules.items()
        },
        "timestamp": datetime.utcnow().isoformat()
    }

# Endpoint-specific rate limiting
def endpoint_rate_limit(rule_name: str):
    """Decorator for endpoint-specific rate limiting"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # This would be integrated with the middleware
            # For now, just return the function result
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# User-specific rate limiting
def user_rate_limit(max_requests: int, window_seconds: int):
    """Decorator for user-specific rate limiting"""
    def decorator(func):
        async def wrapper(user_id: str, *args, **kwargs):
            # This would implement user-specific rate limiting
            # For now, just return the function result
            return await func(user_id, *args, **kwargs)
        return wrapper
    return decorator

# API key validation (for future use)
async def validate_api_key(api_key: str) -> Optional[Dict[str, Any]]:
    """Validate API key and return user info"""
    # This would check against database
    # For now, return mock data
    if api_key.startswith("aap_"):
        return {
            "user_id": "user_123",
            "plan": "premium",
            "limits": {"rpm": 100, "rph": 2000}
        }
    return None

# Dependency for API key authentication
async def get_api_key_user(request: Request) -> Optional[Dict[str, Any]]:
    """Extract and validate API key from request"""
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return await validate_api_key(api_key)
    return None

# Content negotiation
def get_best_content_type(request: Request, supported_types: List[str]) -> str:
    """Get best content type based on Accept header"""
    accept = request.headers.get("Accept", "*/*")

    # Simple content negotiation
    if "application/json" in accept or "*/*" in accept:
        return "application/json"
    elif "application/xml" in accept:
        return "application/xml"
    else:
        return "application/json"  # Default

# Response formatting
def format_response(data: Any, content_type: str, version: str) -> Dict[str, Any]:
    """Format response based on content type and version"""
    base_response = {
        "data": data,
        "api_version": version,
        "timestamp": datetime.utcnow().isoformat()
    }

    if version == "v2":
        base_response["metadata"] = {
            "request_id": str(time.time()),
            "processing_time_ms": 0  # Would be filled by middleware
        }

    return base_response

# Error handling
class APIError(Exception):
    """Custom API error"""

    def __init__(self, message: str, status_code: int = 400, error_code: str = None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or f"error_{status_code}"

def create_error_response(error: APIError, version: str) -> JSONResponse:
    """Create standardized error response"""
    response_data = {
        "error": {
            "message": error.message,
            "code": error.error_code,
            "status_code": error.status_code
        },
        "api_version": version,
        "timestamp": datetime.utcnow().isoformat()
    }

    return JSONResponse(
        status_code=error.status_code,
        content=response_data
    )

# Request validation helpers
def validate_request_data(data: Dict[str, Any], required_fields: List[str]) -> List[str]:
    """Validate required fields in request data"""
    missing = []
    for field in required_fields:
        if field not in data or data[field] is None:
            missing.append(field)
    return missing

def sanitize_input(text: str, max_length: int = 1000) -> str:
    """Sanitize user input"""
    if not text:
        return ""

    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>]', '', text)

    # Truncate if too long
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length] + "..."

    return sanitized.strip()

# Pagination helpers
def paginate_results(results: List[Any], page: int = 1, per_page: int = 20) -> Dict[str, Any]:
    """Paginate results"""
    total = len(results)
    start = (page - 1) * per_page
    end = start + per_page

    return {
        "items": results[start:end],
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": (total + per_page - 1) // per_page,
            "has_next": end < total,
            "has_prev": page > 1
        }
    }

# Caching helpers for API responses
api_response_cache = {}

def cache_api_response(key: str, data: Any, ttl_seconds: int = 300):
    """Cache API response"""
    api_response_cache[key] = {
        "data": data,
        "expires": time.time() + ttl_seconds
    }

def get_cached_api_response(key: str) -> Optional[Any]:
    """Get cached API response"""
    if key in api_response_cache:
        cached = api_response_cache[key]
        if time.time() < cached["expires"]:
            return cached["data"]
        else:
            del api_response_cache[key]
    return None

# Monitoring helpers
def record_api_metrics(endpoint: str, method: str, status_code: int, duration_ms: float):
    """Record API performance metrics"""
    # This would integrate with the monitoring system
    logger.info(f"API Metrics: {method} {endpoint} - {status_code} in {duration_ms:.2f}ms")