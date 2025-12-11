"""
Comprehensive monitoring and metrics system for AI Agent Platform
Real-time metrics, health checks, performance monitoring, and alerting
"""

import time
import psutil
import asyncio
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
import logging
import json
from collections import defaultdict, deque
import threading
import statistics
from dataclasses import dataclass, asdict
import os

logger = logging.getLogger(__name__)

@dataclass
class MetricPoint:
    """Individual metric data point"""
    timestamp: datetime
    value: float
    tags: Dict[str, str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = {}

@dataclass
class MetricSeries:
    """Time series data for a metric"""
    name: str
    points: deque
    max_points: int = 1000

    def add_point(self, value: float, tags: Dict[str, str] = None):
        """Add a data point to the series"""
        point = MetricPoint(datetime.utcnow(), value, tags or {})
        self.points.append(point)

        # Maintain max points limit
        while len(self.points) > self.max_points:
            self.points.popleft()

    def get_recent_points(self, minutes: int = 5) -> List[MetricPoint]:
        """Get points from the last N minutes"""
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        return [p for p in self.points if p.timestamp >= cutoff]

    def get_stats(self, minutes: int = 5) -> Dict[str, Any]:
        """Get statistics for recent points"""
        points = self.get_recent_points(minutes)
        if not points:
            return {"count": 0, "avg": 0, "min": 0, "max": 0}

        values = [p.value for p in points]
        return {
            "count": len(values),
            "avg": statistics.mean(values),
            "min": min(values),
            "max": max(values),
            "latest": values[-1] if values else 0
        }

class MetricsCollector:
    """Collects and stores system and application metrics"""

    def __init__(self):
        self.metrics: Dict[str, MetricSeries] = {}
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, List[float]] = defaultdict(list)

        # Start background collection
        self.collection_task = None
        self.running = False

    def _get_or_create_series(self, name: str) -> MetricSeries:
        """Get or create a metric series"""
        if name not in self.metrics:
            self.metrics[name] = MetricSeries(name)
        return self.metrics[name]

    def increment_counter(self, name: str, value: int = 1, tags: Dict[str, str] = None):
        """Increment a counter metric"""
        self.counters[name] += value
        series = self._get_or_create_series(f"counter:{name}")
        series.add_point(float(self.counters[name]), tags)

    def set_gauge(self, name: str, value: float, tags: Dict[str, str] = None):
        """Set a gauge metric"""
        self.gauges[name] = value
        series = self._get_or_create_series(f"gauge:{name}")
        series.add_point(value, tags)

    def record_histogram(self, name: str, value: float, tags: Dict[str, str] = None):
        """Record a histogram value"""
        self.histograms[name].append(value)
        series = self._get_or_create_series(f"histogram:{name}")
        series.add_point(value, tags)

        # Keep only recent values
        if len(self.histograms[name]) > 1000:
            self.histograms[name] = self.histograms[name][-500:]

    def record_timing(self, name: str, duration_ms: float, tags: Dict[str, str] = None):
        """Record timing metric"""
        series = self._get_or_create_series(f"timing:{name}")
        series.add_point(duration_ms, tags)

    def get_metric_stats(self, name: str, minutes: int = 5) -> Dict[str, Any]:
        """Get statistics for a metric"""
        if name in self.metrics:
            return self.metrics[name].get_stats(minutes)
        return {}

    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all current metric values"""
        result = {
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "histograms": {},
            "series_stats": {}
        }

        # Histogram stats
        for name, values in self.histograms.items():
            if values:
                result["histograms"][name] = {
                    "count": len(values),
                    "avg": statistics.mean(values),
                    "min": min(values),
                    "max": max(values)
                }

        # Series stats
        for name, series in self.metrics.items():
            result["series_stats"][name] = series.get_stats()

        return result

    async def start_collection(self):
        """Start background metric collection"""
        self.running = True
        self.collection_task = asyncio.create_task(self._collect_system_metrics())

    async def stop_collection(self):
        """Stop background metric collection"""
        self.running = False
        if self.collection_task:
            self.collection_task.cancel()
            try:
                await self.collection_task
            except asyncio.CancelledError:
                pass

    async def _collect_system_metrics(self):
        """Collect system-level metrics"""
        while self.running:
            try:
                # CPU usage
                self.set_gauge("system.cpu_percent", psutil.cpu_percent(interval=1))

                # Memory usage
                memory = psutil.virtual_memory()
                self.set_gauge("system.memory_percent", memory.percent)
                self.set_gauge("system.memory_used_mb", memory.used / 1024 / 1024)

                # Disk usage
                disk = psutil.disk_usage('/')
                self.set_gauge("system.disk_percent", disk.percent)
                self.set_gauge("system.disk_used_gb", disk.used / 1024 / 1024 / 1024)

                # Network I/O
                net_io = psutil.net_io_counters()
                self.set_gauge("system.network_bytes_sent", net_io.bytes_sent)
                self.set_gauge("system.network_bytes_recv", net_io.bytes_recv)

                # Process info
                process = psutil.Process()
                self.set_gauge("process.cpu_percent", process.cpu_percent())
                self.set_gauge("process.memory_mb", process.memory_info().rss / 1024 / 1024)
                self.set_gauge("process.threads", process.num_threads())

            except Exception as e:
                logger.error(f"Error collecting system metrics: {e}")

            await asyncio.sleep(30)  # Collect every 30 seconds

class HealthChecker:
    """Health check system for various components"""

    def __init__(self):
        self.checks: Dict[str, Callable] = {}
        self.last_results: Dict[str, Dict[str, Any]] = {}

    def register_check(self, name: str, check_func: Callable):
        """Register a health check function"""
        self.checks[name] = check_func

    async def run_check(self, name: str) -> Dict[str, Any]:
        """Run a specific health check"""
        if name not in self.checks:
            return {"status": "unknown", "message": f"Check {name} not registered"}

        try:
            start_time = time.time()
            result = await self.checks[name]()
            duration = time.time() - start_time

            result["duration_ms"] = round(duration * 1000, 2)
            result["timestamp"] = datetime.utcnow().isoformat()

            self.last_results[name] = result
            return result

        except Exception as e:
            error_result = {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
            self.last_results[name] = error_result
            return error_result

    async def run_all_checks(self) -> Dict[str, Any]:
        """Run all health checks"""
        results = {}
        for name in self.checks:
            results[name] = await self.run_check(name)

        # Overall status
        statuses = [result["status"] for result in results.values()]
        if "error" in statuses:
            overall_status = "unhealthy"
        elif "warning" in statuses:
            overall_status = "degraded"
        else:
            overall_status = "healthy"

        return {
            "overall_status": overall_status,
            "checks": results,
            "timestamp": datetime.utcnow().isoformat()
        }

    def get_last_results(self) -> Dict[str, Dict[str, Any]]:
        """Get last health check results"""
        return dict(self.last_results)

# Global instances
metrics = MetricsCollector()
health_checker = HealthChecker()

# Built-in health checks
async def check_database() -> Dict[str, Any]:
    """Check database connectivity"""
    try:
        # This would be replaced with actual database check
        import sqlite3
        conn = sqlite3.connect("ai_agent_platform.db")
        conn.execute("SELECT 1")
        conn.close()
        return {"status": "healthy", "message": "Database connection OK"}
    except Exception as e:
        return {"status": "error", "message": f"Database error: {e}"}

async def check_redis() -> Dict[str, Any]:
    """Check Redis connectivity"""
    try:
        import redis
        r = redis.Redis()
        r.ping()
        return {"status": "healthy", "message": "Redis connection OK"}
    except Exception as e:
        return {"status": "warning", "message": f"Redis error: {e}"}

async def check_external_apis() -> Dict[str, Any]:
    """Check external API connectivity"""
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            # Check a few key APIs
            apis_to_check = [
                "https://api.github.com",
                "https://httpbin.org/status/200"
            ]

            failed = []
            for api in apis_to_check:
                try:
                    response = await client.get(api, timeout=5)
                    if response.status_code != 200:
                        failed.append(f"{api}: {response.status_code}")
                except Exception as e:
                    failed.append(f"{api}: {str(e)}")

            if failed:
                return {"status": "warning", "message": f"Some APIs failed: {', '.join(failed)}"}
            else:
                return {"status": "healthy", "message": "All external APIs OK"}

    except Exception as e:
        return {"status": "error", "message": f"API check error: {e}"}

async def check_system_resources() -> Dict[str, Any]:
    """Check system resource usage"""
    try:
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        issues = []
        if cpu_percent > 90:
            issues.append(f"High CPU usage: {cpu_percent}%")
        if memory.percent > 90:
            issues.append(f"High memory usage: {memory.percent}%")
        if disk.percent > 90:
            issues.append(f"Low disk space: {disk.percent}%")

        if issues:
            return {"status": "warning", "message": "; ".join(issues)}
        else:
            return {"status": "healthy", "message": "System resources OK"}

    except Exception as e:
        return {"status": "error", "message": f"Resource check error: {e}"}

# Register built-in health checks
health_checker.register_check("database", check_database)
health_checker.register_check("redis", check_redis)
health_checker.register_check("external_apis", check_external_apis)
health_checker.register_check("system_resources", check_system_resources)

class AlertManager:
    """Alert management system"""

    def __init__(self):
        self.alerts: List[Dict[str, Any]] = []
        self.alert_handlers: List[Callable] = []

    def add_alert_handler(self, handler: Callable):
        """Add an alert notification handler"""
        self.alert_handlers.append(handler)

    async def trigger_alert(self, alert_type: str, severity: str, message: str,
                          details: Dict[str, Any] = None):
        """Trigger an alert"""
        alert = {
            "id": str(time.time()),
            "type": alert_type,
            "severity": severity,  # info, warning, error, critical
            "message": message,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat(),
            "resolved": False
        }

        self.alerts.append(alert)

        # Keep only recent alerts
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-50:]

        # Notify handlers
        for handler in self.alert_handlers:
            try:
                await handler(alert)
            except Exception as e:
                logger.error(f"Alert handler error: {e}")

        logger.warning(f"Alert triggered: {alert_type} - {message}")

    async def resolve_alert(self, alert_id: str):
        """Resolve an alert"""
        for alert in self.alerts:
            if alert["id"] == alert_id:
                alert["resolved"] = True
                alert["resolved_at"] = datetime.utcnow().isoformat()
                break

    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get active (unresolved) alerts"""
        return [a for a in self.alerts if not a.get("resolved", False)]

    def get_recent_alerts(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get alerts from the last N hours"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return [a for a in self.alerts if datetime.fromisoformat(a["timestamp"]) >= cutoff]

# Global alert manager
alert_manager = AlertManager()

# Built-in alert handler (logs alerts)
async def log_alert_handler(alert: Dict[str, Any]):
    """Log alerts to file"""
    try:
        log_entry = json.dumps(alert, indent=2)
        with open("logs/alerts.log", "a") as f:
            f.write(f"{log_entry}\n---\n")
    except Exception as e:
        logger.error(f"Failed to log alert: {e}")

# Register default alert handler
alert_manager.add_alert_handler(log_alert_handler)

# Performance monitoring decorators
def monitor_performance(metric_name: str):
    """Decorator to monitor function performance"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                metrics.record_timing(metric_name, duration_ms)
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                metrics.record_timing(f"{metric_name}.error", duration_ms)
                raise e
        return wrapper
    return decorator

def monitor_counter(metric_name: str):
    """Decorator to count function calls"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            metrics.increment_counter(metric_name)
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Monitoring middleware for FastAPI
class MonitoringMiddleware:
    """FastAPI middleware for request monitoring"""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        start_time = time.time()

        # Extract request info
        method = scope["method"]
        path = scope["path"]

        # Process request
        response_status = 200
        response_length = 0

        async def send_wrapper(message):
            nonlocal response_status, response_length
            if message["type"] == "http.response.start":
                response_status = message["status"]
            elif message["type"] == "http.response.body":
                response_length += len(message.get("body", b""))
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)

            # Record metrics
            duration_ms = (time.time() - start_time) * 1000
            metrics.record_timing("http.request.duration", duration_ms, {"method": method, "path": path})
            metrics.increment_counter("http.requests.total", tags={"method": method, "status": str(response_status)})
            metrics.set_gauge("http.response.size", response_length, {"method": method, "path": path})

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            metrics.record_timing("http.request.error.duration", duration_ms, {"method": method, "path": path})
            metrics.increment_counter("http.requests.errors", tags={"method": method, "path": path})
            raise e

# Helper functions
async def record_task_execution(agent_name: str, duration_ms: float, success: bool):
    """Record task execution metrics"""
    metrics.record_timing(f"task.{agent_name}.execution_time", duration_ms)
    status = "success" if success else "failure"
    metrics.increment_counter(f"task.{agent_name}.{status}")

async def record_api_call(endpoint: str, duration_ms: float, status_code: int):
    """Record API call metrics"""
    metrics.record_timing(f"api.{endpoint}.duration", duration_ms)
    metrics.increment_counter("api.calls.total", tags={"endpoint": endpoint, "status": str(status_code)})

async def check_health() -> Dict[str, Any]:
    """Comprehensive health check"""
    return await health_checker.run_all_checks()

async def get_system_status() -> Dict[str, Any]:
    """Get complete system status"""
    return {
        "metrics": metrics.get_all_metrics(),
        "health": await check_health(),
        "alerts": alert_manager.get_active_alerts(),
        "timestamp": datetime.utcnow().isoformat()
    }