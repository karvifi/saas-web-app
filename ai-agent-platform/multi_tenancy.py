"""
Multi-tenancy support for AI Agent Platform
Organization-based deployments, tenant isolation, and resource management
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from pydantic import BaseModel
import hashlib
import json

logger = logging.getLogger(__name__)

@dataclass
class Tenant:
    """Tenant (organization) data structure"""
    tenant_id: str
    name: str
    domain: str
    created_at: datetime
    status: str  # active, suspended, inactive
    plan: str  # starter, professional, enterprise
    settings: Dict[str, Any]
    limits: Dict[str, Any]
    features: List[str]
    admin_users: List[str]
    subscription_end: Optional[datetime]

@dataclass
class TenantUser:
    """Tenant user relationship"""
    user_id: str
    tenant_id: str
    role: str  # admin, member, guest
    joined_at: datetime
    permissions: List[str]

class TenantManager:
    """Multi-tenant management system"""

    def __init__(self):
        # In-memory tenant storage (in production, use database)
        self.tenants: Dict[str, Tenant] = {}
        self.tenant_users: Dict[str, List[TenantUser]] = {}

        # Default limits by plan
        self.plan_limits = {
            "starter": {
                "max_users": 5,
                "max_tasks_per_day": 100,
                "max_storage_mb": 100,
                "api_rate_limit": 100
            },
            "professional": {
                "max_users": 50,
                "max_tasks_per_day": 1000,
                "max_storage_mb": 1000,
                "api_rate_limit": 1000
            },
            "enterprise": {
                "max_users": 1000,
                "max_tasks_per_day": 10000,
                "max_storage_mb": 10000,
                "api_rate_limit": 10000
            }
        }

        # Default features by plan
        self.plan_features = {
            "starter": ["basic_agents", "task_execution", "file_upload"],
            "professional": ["basic_agents", "task_execution", "file_upload", "analytics", "api_access"],
            "enterprise": ["basic_agents", "task_execution", "file_upload", "analytics", "api_access", "custom_agents", "white_label"]
        }

    def _generate_tenant_id(self) -> str:
        """Generate unique tenant ID"""
        return hashlib.md5(f"tenant_{datetime.utcnow().isoformat()}".encode()).hexdigest()[:12]

    async def create_tenant(self, name: str, domain: str, admin_user_id: str,
                          plan: str = "starter") -> str:
        """Create a new tenant"""
        if plan not in self.plan_limits:
            raise ValueError(f"Invalid plan: {plan}")

        tenant_id = self._generate_tenant_id()

        tenant = Tenant(
            tenant_id=tenant_id,
            name=name,
            domain=domain,
            created_at=datetime.utcnow(),
            status="active",
            plan=plan,
            settings={
                "theme": "default",
                "timezone": "UTC",
                "language": "en"
            },
            limits=self.plan_limits[plan],
            features=self.plan_features[plan],
            admin_users=[admin_user_id],
            subscription_end=None
        )

        self.tenants[tenant_id] = tenant
        self.tenant_users[tenant_id] = []

        # Add admin user
        await self.add_user_to_tenant(tenant_id, admin_user_id, "admin")

        logger.info(f"Created tenant: {tenant_id} ({name})")
        return tenant_id

    async def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID"""
        return self.tenants.get(tenant_id)

    async def get_tenant_by_domain(self, domain: str) -> Optional[Tenant]:
        """Get tenant by domain"""
        for tenant in self.tenants.values():
            if tenant.domain == domain:
                return tenant
        return None

    async def update_tenant(self, tenant_id: str, updates: Dict[str, Any]) -> bool:
        """Update tenant settings"""
        tenant = self.tenants.get(tenant_id)
        if not tenant:
            return False

        for key, value in updates.items():
            if hasattr(tenant, key):
                setattr(tenant, key, value)

        logger.info(f"Updated tenant: {tenant_id}")
        return True

    async def suspend_tenant(self, tenant_id: str) -> bool:
        """Suspend a tenant"""
        tenant = self.tenants.get(tenant_id)
        if not tenant:
            return False

        tenant.status = "suspended"
        logger.warning(f"Suspended tenant: {tenant_id}")
        return True

    async def activate_tenant(self, tenant_id: str) -> bool:
        """Activate a tenant"""
        tenant = self.tenants.get(tenant_id)
        if not tenant:
            return False

        tenant.status = "active"
        logger.info(f"Activated tenant: {tenant_id}")
        return True

    async def add_user_to_tenant(self, tenant_id: str, user_id: str, role: str = "member") -> bool:
        """Add user to tenant"""
        if tenant_id not in self.tenants:
            return False

        tenant = self.tenants[tenant_id]

        # Check user limit
        if len(self.tenant_users[tenant_id]) >= tenant.limits["max_users"]:
            raise ValueError("Tenant user limit reached")

        # Check if user already in tenant
        for tenant_user in self.tenant_users[tenant_id]:
            if tenant_user.user_id == user_id:
                return False

        tenant_user = TenantUser(
            user_id=user_id,
            tenant_id=tenant_id,
            role=role,
            joined_at=datetime.utcnow(),
            permissions=self._get_role_permissions(role)
        )

        self.tenant_users[tenant_id].append(tenant_user)
        logger.info(f"Added user {user_id} to tenant {tenant_id} as {role}")
        return True

    async def remove_user_from_tenant(self, tenant_id: str, user_id: str) -> bool:
        """Remove user from tenant"""
        if tenant_id not in self.tenant_users:
            return False

        original_length = len(self.tenant_users[tenant_id])
        self.tenant_users[tenant_id] = [
            tu for tu in self.tenant_users[tenant_id] if tu.user_id != user_id
        ]

        removed = len(self.tenant_users[tenant_id]) < original_length
        if removed:
            logger.info(f"Removed user {user_id} from tenant {tenant_id}")
        return removed

    async def get_tenant_users(self, tenant_id: str) -> List[TenantUser]:
        """Get all users in a tenant"""
        return self.tenant_users.get(tenant_id, [])

    async def get_user_tenants(self, user_id: str) -> List[TenantUser]:
        """Get all tenants for a user"""
        user_tenants = []
        for tenant_users in self.tenant_users.values():
            for tenant_user in tenant_users:
                if tenant_user.user_id == user_id:
                    user_tenants.append(tenant_user)
        return user_tenants

    def _get_role_permissions(self, role: str) -> List[str]:
        """Get permissions for a role"""
        permissions = {
            "admin": ["manage_users", "manage_settings", "view_analytics", "manage_billing", "full_access"],
            "member": ["execute_tasks", "view_own_data", "upload_files"],
            "guest": ["view_public_data", "execute_limited_tasks"]
        }
        return permissions.get(role, [])

    async def check_tenant_limits(self, tenant_id: str, resource: str, current_usage: int) -> bool:
        """Check if tenant is within limits for a resource"""
        tenant = self.tenants.get(tenant_id)
        if not tenant:
            return False

        limit = tenant.limits.get(resource)
        if limit is None:
            return True  # No limit set

        return current_usage < limit

    async def get_tenant_usage(self, tenant_id: str) -> Dict[str, Any]:
        """Get tenant resource usage"""
        tenant = self.tenants.get(tenant_id)
        if not tenant:
            return {}

        # Mock usage data - in production, this would be calculated from actual usage
        return {
            "users": len(self.tenant_users.get(tenant_id, [])),
            "tasks_today": 0,  # Would be calculated from task logs
            "storage_used_mb": 0,  # Would be calculated from file storage
            "api_calls_today": 0  # Would be calculated from API logs
        }

    async def upgrade_tenant_plan(self, tenant_id: str, new_plan: str) -> bool:
        """Upgrade tenant to a higher plan"""
        tenant = self.tenants.get(tenant_id)
        if not tenant:
            return False

        if new_plan not in self.plan_limits:
            raise ValueError(f"Invalid plan: {new_plan}")

        tenant.plan = new_plan
        tenant.limits = self.plan_limits[new_plan]
        tenant.features = self.plan_features[new_plan]

        logger.info(f"Upgraded tenant {tenant_id} to plan {new_plan}")
        return True

class TenantMiddleware:
    """Middleware for tenant context"""

    def __init__(self, app, tenant_manager: TenantManager):
        self.app = app
        self.tenant_manager = tenant_manager

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        # Extract tenant from domain or header
        headers = dict(scope.get("headers", []))
        domain = None
        tenant_id = None

        # Check for tenant header
        tenant_header = headers.get(b'x-tenant-id')
        if tenant_header:
            tenant_id = tenant_header.decode()

        # Check domain
        host = headers.get(b'host', b'').decode().split(':')[0]
        if not tenant_id and '.' in host:
            # Extract subdomain (e.g., company.aiagentplatform.com -> company)
            parts = host.split('.')
            if len(parts) >= 3 and parts[-2:] == ['aiagentplatform', 'com']:
                subdomain = parts[0]
                tenant = await self.tenant_manager.get_tenant_by_domain(subdomain)
                if tenant:
                    tenant_id = tenant.tenant_id

        # Set tenant context
        scope["tenant_id"] = tenant_id

        return await self.app(scope, receive, send)

# Dependency for tenant context
async def get_current_tenant(request: Request) -> Optional[Tenant]:
    """Get current tenant from request"""
    tenant_id = getattr(request.state, "tenant_id", None)
    if tenant_id:
        return await tenant_manager.get_tenant(tenant_id)
    return None

async def require_tenant_access(required_permissions: List[str] = None):
    """Dependency to require tenant access and permissions"""
    async def dependency(request: Request, user_id: str = Query(...)):
        tenant_id = getattr(request.state, "tenant_id", None)
        if not tenant_id:
            raise HTTPException(status_code=400, detail="No tenant context")

        tenant = await tenant_manager.get_tenant(tenant_id)
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")

        if tenant.status != "active":
            raise HTTPException(status_code=403, detail="Tenant is not active")

        # Check user permissions
        tenant_users = await tenant_manager.get_tenant_users(tenant_id)
        user_tenant = next((tu for tu in tenant_users if tu.user_id == user_id), None)

        if not user_tenant:
            raise HTTPException(status_code=403, detail="User not in tenant")

        if required_permissions:
            missing_perms = [p for p in required_permissions if p not in user_tenant.permissions]
            if missing_perms:
                raise HTTPException(
                    status_code=403,
                    detail=f"Missing permissions: {', '.join(missing_perms)}"
                )

        return tenant

    return dependency

# Global tenant manager
tenant_manager = TenantManager()

# FastAPI router for tenant management
router = APIRouter(prefix="/tenants", tags=["tenants"])

@router.post("/")
async def create_tenant(
    name: str,
    domain: str,
    admin_user_id: str,
    plan: str = "starter"
):
    """Create a new tenant"""
    try:
        tenant_id = await tenant_manager.create_tenant(name, domain, admin_user_id, plan)
        tenant = await tenant_manager.get_tenant(tenant_id)
        return {"tenant_id": tenant_id, "tenant": asdict(tenant)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{tenant_id}")
async def get_tenant_info(tenant_id: str):
    """Get tenant information"""
    tenant = await tenant_manager.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    return asdict(tenant)

@router.put("/{tenant_id}")
async def update_tenant(
    tenant_id: str,
    updates: Dict[str, Any],
    admin_user_id: str
):
    """Update tenant settings"""
    # Check if user is admin
    tenant_users = await tenant_manager.get_tenant_users(tenant_id)
    user_tenant = next((tu for tu in tenant_users if tu.user_id == admin_user_id), None)

    if not user_tenant or user_tenant.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    success = await tenant_manager.update_tenant(tenant_id, updates)
    if not success:
        raise HTTPException(status_code=404, detail="Tenant not found")

    return {"message": "Tenant updated"}

@router.post("/{tenant_id}/users")
async def add_tenant_user(
    tenant_id: str,
    user_id: str,
    role: str = "member",
    admin_user_id: str = Query(...)
):
    """Add user to tenant"""
    # Check admin permissions
    tenant_users = await tenant_manager.get_tenant_users(tenant_id)
    admin_tenant = next((tu for tu in tenant_users if tu.user_id == admin_user_id), None)

    if not admin_tenant or admin_tenant.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        success = await tenant_manager.add_user_to_tenant(tenant_id, user_id, role)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to add user")

        return {"message": f"User {user_id} added to tenant as {role}"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{tenant_id}/users/{user_id}")
async def remove_tenant_user(
    tenant_id: str,
    user_id: str,
    admin_user_id: str
):
    """Remove user from tenant"""
    # Check admin permissions
    tenant_users = await tenant_manager.get_tenant_users(tenant_id)
    admin_tenant = next((tu for tu in tenant_users if tu.user_id == admin_user_id), None)

    if not admin_tenant or admin_tenant.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    success = await tenant_manager.remove_user_from_tenant(tenant_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not in tenant")

    return {"message": "User removed from tenant"}

@router.get("/{tenant_id}/users")
async def get_tenant_users(tenant_id: str):
    """Get tenant users"""
    users = await tenant_manager.get_tenant_users(tenant_id)
    return {"users": [asdict(u) for u in users], "count": len(users)}

@router.get("/user/{user_id}")
async def get_user_tenants(user_id: str):
    """Get user's tenants"""
    tenants = await tenant_manager.get_user_tenants(user_id)
    return {"tenants": [asdict(t) for t in tenants], "count": len(tenants)}

@router.get("/{tenant_id}/usage")
async def get_tenant_usage(tenant_id: str):
    """Get tenant usage statistics"""
    usage = await tenant_manager.get_tenant_usage(tenant_id)
    limits = {}

    tenant = await tenant_manager.get_tenant(tenant_id)
    if tenant:
        limits = tenant.limits

    return {"usage": usage, "limits": limits}

@router.post("/{tenant_id}/upgrade")
async def upgrade_tenant_plan(
    tenant_id: str,
    new_plan: str,
    admin_user_id: str
):
    """Upgrade tenant plan"""
    # Check admin permissions
    tenant_users = await tenant_manager.get_tenant_users(tenant_id)
    admin_tenant = next((tu for tu in tenant_users if tu.user_id == admin_user_id), None)

    if not admin_tenant or admin_tenant.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        success = await tenant_manager.upgrade_tenant_plan(tenant_id, new_plan)
        if not success:
            raise HTTPException(status_code=404, detail="Tenant not found")

        return {"message": f"Tenant upgraded to {new_plan} plan"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{tenant_id}/suspend")
async def suspend_tenant(tenant_id: str):
    """Suspend tenant (admin only)"""
    success = await tenant_manager.suspend_tenant(tenant_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tenant not found")

    return {"message": "Tenant suspended"}

@router.post("/{tenant_id}/activate")
async def activate_tenant(tenant_id: str):
    """Activate tenant (admin only)"""
    success = await tenant_manager.activate_tenant(tenant_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tenant not found")

    return {"message": "Tenant activated"}

# Utility functions
async def get_tenant_context(user_id: str, tenant_id: Optional[str] = None) -> Dict[str, Any]:
    """Get tenant context for a user"""
    if not tenant_id:
        # Get user's default tenant
        user_tenants = await tenant_manager.get_user_tenants(user_id)
        if user_tenants:
            tenant_id = user_tenants[0].tenant_id

    if not tenant_id:
        return {"tenant": None, "permissions": []}

    tenant = await tenant_manager.get_tenant(tenant_id)
    if not tenant:
        return {"tenant": None, "permissions": []}

    tenant_users = await tenant_manager.get_tenant_users(tenant_id)
    user_tenant = next((tu for tu in tenant_users if tu.user_id == user_id), None)

    if not user_tenant:
        return {"tenant": None, "permissions": []}

    return {
        "tenant": asdict(tenant),
        "permissions": user_tenant.permissions,
        "role": user_tenant.role
    }

async def check_tenant_resource_access(tenant_id: str, user_id: str, resource: str) -> bool:
    """Check if user has access to a resource in tenant"""
    tenant_users = await tenant_manager.get_tenant_users(tenant_id)
    user_tenant = next((tu for tu in tenant_users if tu.user_id == user_id), None)

    if not user_tenant:
        return False

    # Define resource permissions
    resource_permissions = {
        "tasks": ["execute_tasks"],
        "files": ["upload_files"],
        "analytics": ["view_analytics"],
        "settings": ["manage_settings"],
        "users": ["manage_users"],
        "billing": ["manage_billing"]
    }

    required_perms = resource_permissions.get(resource, [])
    return all(perm in user_tenant.permissions for perm in required_perms)

# Tenant-aware rate limiting
async def get_tenant_rate_limit(tenant_id: str) -> Dict[str, Any]:
    """Get rate limit for tenant"""
    tenant = await tenant_manager.get_tenant(tenant_id)
    if not tenant:
        return {"rpm": 10, "rph": 100}  # Very restrictive for unknown tenants

    return {
        "rpm": tenant.limits.get("api_rate_limit", 100),
        "rph": tenant.limits.get("api_rate_limit", 100) * 24
    }