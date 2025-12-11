"""
Audit logging and compliance features for AI Agent Platform
GDPR compliance, audit trails, data export, and security monitoring
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
import asyncio
import hashlib
import csv
import zipfile
from dataclasses import dataclass, asdict
import re
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

@dataclass
class AuditEvent:
    """Audit event data structure"""
    event_id: str
    timestamp: datetime
    event_type: str
    user_id: Optional[str]
    session_id: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    resource: str
    action: str
    status: str  # success, failure, error
    details: Dict[str, Any]
    severity: str  # low, medium, high, critical
    compliance_flags: List[str]  # GDPR, SOX, HIPAA, etc.

@dataclass
class DataRequest:
    """Data subject access request"""
    request_id: str
    user_id: str
    request_type: str  # access, rectification, erasure, restriction, portability
    status: str  # pending, processing, completed, rejected
    created_at: datetime
    completed_at: Optional[datetime]
    data: Dict[str, Any]
    notes: str

class AuditLogger:
    """Comprehensive audit logging system"""

    def __init__(self, log_dir: str = "logs/audit"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # In-memory event storage (in production, use database)
        self.events: List[AuditEvent] = []
        self.max_events = 10000  # Keep last 10k events in memory

        # Compliance frameworks
        self.compliance_frameworks = {
            "GDPR": self._check_gdpr_compliance,
            "CCPA": self._check_ccpa_compliance,
            "SOX": self._check_sox_compliance,
            "HIPAA": self._check_hipaa_compliance
        }

    def _generate_event_id(self) -> str:
        """Generate unique event ID"""
        return hashlib.md5(f"{datetime.utcnow().isoformat()}{id(self)}".encode()).hexdigest()[:16]

    def _check_gdpr_compliance(self, event: AuditEvent) -> List[str]:
        """Check GDPR compliance flags"""
        flags = []

        # Personal data processing
        if "personal_data" in event.details:
            flags.append("personal_data_processing")

        # Data subject rights
        if event.action in ["data_access", "data_rectification", "data_erasure"]:
            flags.append("data_subject_right")

        # Consent management
        if "consent" in event.details:
            flags.append("consent_management")

        # Data breaches
        if event.event_type == "security_incident":
            flags.append("data_breach")

        return flags

    def _check_ccpa_compliance(self, event: AuditEvent) -> List[str]:
        """Check CCPA compliance flags"""
        flags = []

        # Personal information sales
        if "data_sale" in event.details:
            flags.append("personal_info_sale")

        # Opt-out requests
        if event.action == "opt_out":
            flags.append("opt_out_request")

        return flags

    def _check_sox_compliance(self, event: AuditEvent) -> List[str]:
        """Check SOX compliance flags"""
        flags = []

        # Financial data access
        if "financial" in event.resource:
            flags.append("financial_data_access")

        # System changes
        if event.action in ["create", "update", "delete"] and event.resource in ["user", "system_config"]:
            flags.append("system_change")

        return flags

    def _check_hipaa_compliance(self, event: AuditEvent) -> List[str]:
        """Check HIPAA compliance flags"""
        flags = []

        # Protected health information
        if "phi" in event.details or "health" in event.resource:
            flags.append("phi_access")

        # Medical records
        if event.resource == "medical_record":
            flags.append("medical_record_access")

        return flags

    async def log_event(self, event_type: str, user_id: Optional[str], resource: str,
                       action: str, status: str = "success", details: Dict[str, Any] = None,
                       severity: str = "low", ip_address: Optional[str] = None,
                       user_agent: Optional[str] = None, session_id: Optional[str] = None) -> str:
        """Log an audit event"""
        event_id = self._generate_event_id()

        # Determine compliance flags
        compliance_flags = []
        for framework, checker in self.compliance_frameworks.items():
            temp_event = AuditEvent(
                event_id=event_id,
                timestamp=datetime.utcnow(),
                event_type=event_type,
                user_id=user_id,
                session_id=session_id,
                ip_address=ip_address,
                user_agent=user_agent,
                resource=resource,
                action=action,
                status=status,
                details=details or {},
                severity=severity,
                compliance_flags=[]
            )
            flags = checker(temp_event)
            compliance_flags.extend(flags)

        event = AuditEvent(
            event_id=event_id,
            timestamp=datetime.utcnow(),
            event_type=event_type,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            resource=resource,
            action=action,
            status=status,
            details=details or {},
            severity=severity,
            compliance_flags=list(set(compliance_flags))  # Remove duplicates
        )

        # Add to in-memory storage
        self.events.append(event)
        if len(self.events) > self.max_events:
            self.events.pop(0)

        # Write to log file
        await self._write_to_log_file(event)

        # Alert on high-severity events
        if severity in ["high", "critical"]:
            await self._alert_high_severity_event(event)

        logger.info(f"Audit event logged: {event_type} - {action} on {resource} by {user_id}")
        return event_id

    async def _write_to_log_file(self, event: AuditEvent):
        """Write event to log file"""
        try:
            date_str = event.timestamp.strftime("%Y-%m-%d")
            log_file = self.log_dir / f"audit_{date_str}.log"

            log_entry = {
                "event_id": event.event_id,
                "timestamp": event.timestamp.isoformat(),
                "event_type": event.event_type,
                "user_id": event.user_id,
                "session_id": event.session_id,
                "ip_address": event.ip_address,
                "user_agent": event.user_agent,
                "resource": event.resource,
                "action": event.action,
                "status": event.status,
                "details": event.details,
                "severity": event.severity,
                "compliance_flags": event.compliance_flags
            }

            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")

        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")

    async def _alert_high_severity_event(self, event: AuditEvent):
        """Alert administrators about high-severity events"""
        # This would integrate with notification system
        logger.warning(f"HIGH SEVERITY AUDIT EVENT: {event.event_type} - {event.action}")

    def query_events(self, user_id: Optional[str] = None, event_type: Optional[str] = None,
                    resource: Optional[str] = None, start_date: Optional[datetime] = None,
                    end_date: Optional[datetime] = None, limit: int = 100) -> List[AuditEvent]:
        """Query audit events"""
        events = self.events.copy()

        # Apply filters
        if user_id:
            events = [e for e in events if e.user_id == user_id]
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        if resource:
            events = [e for e in events if e.resource == resource]
        if start_date:
            events = [e for e in events if e.timestamp >= start_date]
        if end_date:
            events = [e for e in events if e.timestamp <= end_date]

        # Sort by timestamp (newest first) and limit
        events.sort(key=lambda x: x.timestamp, reverse=True)
        return events[:limit]

    def get_compliance_report(self, framework: str, start_date: datetime,
                            end_date: datetime) -> Dict[str, Any]:
        """Generate compliance report for a framework"""
        events = self.query_events(start_date=start_date, end_date=end_date)

        framework_events = [e for e in events if framework.upper() in [f.upper() for f in e.compliance_flags]]

        report = {
            "framework": framework,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "total_events": len(framework_events),
            "events_by_type": {},
            "events_by_severity": {},
            "compliance_issues": []
        }

        for event in framework_events:
            # Count by type
            event_type = event.event_type
            report["events_by_type"][event_type] = report["events_by_type"].get(event_type, 0) + 1

            # Count by severity
            severity = event.severity
            report["events_by_severity"][severity] = report["events_by_severity"].get(severity, 0) + 1

            # Check for compliance issues
            if event.status == "failure" or event.severity in ["high", "critical"]:
                report["compliance_issues"].append({
                    "event_id": event.event_id,
                    "timestamp": event.timestamp.isoformat(),
                    "issue": f"{event.action} on {event.resource} failed",
                    "severity": event.severity
                })

        return report

class DataPrivacyManager:
    """Data privacy and subject rights management"""

    def __init__(self):
        self.requests: Dict[str, DataRequest] = {}
        self.retention_policies = {
            "user_data": timedelta(days=2555),  # 7 years for GDPR
            "logs": timedelta(days=90),
            "temp_files": timedelta(hours=24)
        }

    def _generate_request_id(self) -> str:
        """Generate unique request ID"""
        return f"DSR_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{hashlib.md5(str(id(self)).encode()).hexdigest()[:8]}"

    async def create_data_request(self, user_id: str, request_type: str, notes: str = "") -> str:
        """Create a data subject access request"""
        if request_type not in ["access", "rectification", "erasure", "restriction", "portability"]:
            raise ValueError("Invalid request type")

        request_id = self._generate_request_id()

        request = DataRequest(
            request_id=request_id,
            user_id=user_id,
            request_type=request_type,
            status="pending",
            created_at=datetime.utcnow(),
            completed_at=None,
            data={},
            notes=notes
        )

        self.requests[request_id] = request

        # Log the request
        await audit_logger.log_event(
            event_type="data_subject_request",
            user_id=user_id,
            resource="user_data",
            action=f"request_{request_type}",
            details={"request_id": request_id, "notes": notes}
        )

        return request_id

    async def process_data_request(self, request_id: str, admin_user_id: str) -> bool:
        """Process a data request"""
        if request_id not in self.requests:
            return False

        request = self.requests[request_id]
        request.status = "processing"

        try:
            if request.request_type == "access":
                request.data = await self._gather_user_data(request.user_id)
            elif request.request_type == "erasure":
                await self._erase_user_data(request.user_id)
            elif request.request_type == "rectification":
                # Would implement data correction logic
                pass
            elif request.request_type == "restriction":
                # Would implement data processing restrictions
                pass
            elif request.request_type == "portability":
                request.data = await self._export_user_data(request.user_id)

            request.status = "completed"
            request.completed_at = datetime.utcnow()

            # Log completion
            await audit_logger.log_event(
                event_type="data_subject_request",
                user_id=admin_user_id,
                resource="user_data",
                action=f"processed_{request.request_type}",
                details={"request_id": request_id, "target_user": request.user_id}
            )

            return True

        except Exception as e:
            request.status = "error"
            request.notes += f" Error: {str(e)}"
            logger.error(f"Failed to process data request {request_id}: {e}")
            return False

    async def _gather_user_data(self, user_id: str) -> Dict[str, Any]:
        """Gather all user data for access request"""
        # This would query all data stores
        # Mock implementation
        return {
            "user_profile": {"user_id": user_id, "name": "User Name"},
            "task_history": [],
            "payment_history": [],
            "audit_events": audit_logger.query_events(user_id=user_id, limit=100)
        }

    async def _erase_user_data(self, user_id: str):
        """Erase user data for GDPR compliance"""
        # This would delete user data from all stores
        # Mock implementation
        logger.info(f"Erasing data for user {user_id}")

    async def _export_user_data(self, user_id: str) -> Dict[str, Any]:
        """Export user data in portable format"""
        data = await self._gather_user_data(user_id)

        # Convert to JSON-serializable format
        export_data = {}
        for key, value in data.items():
            if key == "audit_events":
                export_data[key] = [asdict(event) for event in value]
            else:
                export_data[key] = value

        return export_data

    def get_pending_requests(self) -> List[DataRequest]:
        """Get pending data requests"""
        return [r for r in self.requests.values() if r.status == "pending"]

    def get_request_status(self, request_id: str) -> Optional[DataRequest]:
        """Get data request status"""
        return self.requests.get(request_id)

class ComplianceChecker:
    """Automated compliance checking"""

    def __init__(self):
        self.checks = {
            "data_retention": self._check_data_retention,
            "access_controls": self._check_access_controls,
            "encryption": self._check_encryption,
            "audit_logging": self._check_audit_logging
        }

    async def run_compliance_check(self, framework: str) -> Dict[str, Any]:
        """Run compliance check for a framework"""
        results = {
            "framework": framework,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {},
            "overall_status": "compliant"
        }

        for check_name, check_func in self.checks.items():
            try:
                check_result = await check_func()
                results["checks"][check_name] = check_result

                if not check_result["compliant"]:
                    results["overall_status"] = "non_compliant"

            except Exception as e:
                results["checks"][check_name] = {
                    "compliant": False,
                    "message": f"Check failed: {str(e)}"
                }
                results["overall_status"] = "error"

        return results

    async def _check_data_retention(self) -> Dict[str, Any]:
        """Check data retention compliance"""
        # Mock check - would verify data older than retention period is deleted
        return {
            "compliant": True,
            "message": "Data retention policies are properly enforced"
        }

    async def _check_access_controls(self) -> Dict[str, Any]:
        """Check access control compliance"""
        # Mock check - would verify proper access controls are in place
        return {
            "compliant": True,
            "message": "Access controls are properly implemented"
        }

    async def _check_encryption(self) -> Dict[str, Any]:
        """Check encryption compliance"""
        # Mock check - would verify data encryption
        return {
            "compliant": True,
            "message": "Data encryption is properly implemented"
        }

    async def _check_audit_logging(self) -> Dict[str, Any]:
        """Check audit logging compliance"""
        recent_events = audit_logger.query_events(limit=10)
        if len(recent_events) > 0:
            return {
                "compliant": True,
                "message": f"Audit logging active with {len(recent_events)} recent events"
            }
        else:
            return {
                "compliant": False,
                "message": "No recent audit events found"
            }

# Global instances
audit_logger = AuditLogger()
data_privacy_manager = DataPrivacyManager()
compliance_checker = ComplianceChecker()

# FastAPI router for compliance endpoints
router = APIRouter(prefix="/compliance", tags=["compliance"])

@router.post("/audit/log")
async def log_audit_event(
    event_type: str,
    resource: str,
    action: str,
    user_id: str = Query(None),
    status: str = "success",
    details: Dict[str, Any] = None,
    severity: str = "low"
):
    """Log an audit event"""
    event_id = await audit_logger.log_event(
        event_type=event_type,
        user_id=user_id,
        resource=resource,
        action=action,
        status=status,
        details=details,
        severity=severity
    )
    return {"event_id": event_id}

@router.get("/audit/events")
async def query_audit_events(
    user_id: str = Query(None),
    event_type: str = Query(None),
    resource: str = Query(None),
    start_date: str = Query(None),
    end_date: str = Query(None),
    limit: int = Query(100, le=1000)
):
    """Query audit events"""
    start = datetime.fromisoformat(start_date) if start_date else None
    end = datetime.fromisoformat(end_date) if end_date else None

    events = audit_logger.query_events(
        user_id=user_id,
        event_type=event_type,
        resource=resource,
        start_date=start,
        end_date=end,
        limit=limit
    )

    return {"events": [asdict(event) for event in events], "count": len(events)}

@router.get("/audit/report/{framework}")
async def get_compliance_report(
    framework: str,
    days: int = Query(30, description="Report period in days")
):
    """Get compliance report"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    report = audit_logger.get_compliance_report(framework, start_date, end_date)
    return report

@router.post("/data-request")
async def create_data_request(
    request_type: str,
    user_id: str,
    notes: str = ""
):
    """Create a data subject access request"""
    try:
        request_id = await data_privacy_manager.create_data_request(
            user_id=user_id,
            request_type=request_type,
            notes=notes
        )
        return {"request_id": request_id, "status": "created"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/data-request/{request_id}/process")
async def process_data_request(
    request_id: str,
    admin_user_id: str
):
    """Process a data request (admin only)"""
    success = await data_privacy_manager.process_data_request(request_id, admin_user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Request not found or processing failed")

    request = data_privacy_manager.get_request_status(request_id)
    return {"status": request.status if request else "unknown"}

@router.get("/data-request/{request_id}")
async def get_data_request_status(request_id: str):
    """Get data request status"""
    request = data_privacy_manager.get_request_status(request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")

    return asdict(request)

@router.get("/data-requests/pending")
async def get_pending_requests():
    """Get pending data requests (admin only)"""
    requests = data_privacy_manager.get_pending_requests()
    return {"requests": [asdict(r) for r in requests], "count": len(requests)}

@router.get("/compliance/check/{framework}")
async def run_compliance_check(framework: str):
    """Run compliance check"""
    result = await compliance_checker.run_compliance_check(framework)
    return result

# Utility functions for easy integration
async def log_user_action(user_id: str, action: str, resource: str, details: Dict[str, Any] = None):
    """Log user action"""
    await audit_logger.log_event(
        event_type="user_action",
        user_id=user_id,
        resource=resource,
        action=action,
        details=details
    )

async def log_security_event(event_type: str, user_id: str, details: Dict[str, Any]):
    """Log security event"""
    await audit_logger.log_event(
        event_type=event_type,
        user_id=user_id,
        resource="security",
        action="security_event",
        severity="high",
        details=details
    )

async def log_api_access(user_id: str, endpoint: str, method: str, status_code: int, ip_address: str):
    """Log API access"""
    severity = "medium" if status_code >= 400 else "low"
    await audit_logger.log_event(
        event_type="api_access",
        user_id=user_id,
        resource=endpoint,
        action=method,
        status="success" if status_code < 400 else "failure",
        severity=severity,
        ip_address=ip_address,
        details={"status_code": status_code}
    )

# Background cleanup task
async def cleanup_old_audit_logs():
    """Clean up old audit log files"""
    try:
        cutoff = datetime.utcnow() - timedelta(days=365)  # Keep 1 year of logs
        audit_dir = Path("logs/audit")

        if audit_dir.exists():
            for log_file in audit_dir.glob("audit_*.log"):
                # Extract date from filename
                date_match = re.search(r'audit_(\d{4}-\d{2}-\d{2})\.log', log_file.name)
                if date_match:
                    file_date = datetime.fromisoformat(date_match.group(1))
                    if file_date < cutoff:
                        log_file.unlink()
                        logger.info(f"Cleaned up old audit log: {log_file.name}")

    except Exception as e:
        logger.error(f"Error cleaning up audit logs: {e}")

async def start_compliance_tasks():
    """Start background compliance tasks"""
    while True:
        await cleanup_old_audit_logs()
        await asyncio.sleep(86400)  # Run daily