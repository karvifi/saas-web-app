# backend/userprofiles.py
import json
import os
from pathlib import Path
from typing import Dict, Any, List
from loguru import logger
from datetime import datetime

class UserProfileManager:
    def __init__(self, data_dir: str = "data/user_profiles", db_path: str = None):
        if db_path:
            # For backward compatibility with tests
            data_dir = db_path
        self.data_dir = Path(data_dir)
        self.logger = logger  # Assign logger first
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self.logger.error(f"Failed to create data directory {self.data_dir}: {e}")
            # Fallback to temp directory
            import tempfile
            self.data_dir = Path(tempfile.gettempdir()) / "ai_agent_profiles"
            self.data_dir.mkdir(parents=True, exist_ok=True)
        self.logger.info(f" UserProfileManager initialized at {self.data_dir}")
    
    def _get_profile_path(self, user_id: str) -> Path:
        """Safe filename for user_id"""
        safe_id = user_id.replace("/", "_").replace("\\", "_")
        return self.data_dir / f"{safe_id}.json"
    
    def get_user(self, user_id: str) -> Dict[str, Any]:
        """Load user profile"""
        try:
            path = self._get_profile_path(user_id)
            
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    profile = json.load(f)
                    self.logger.debug(f"Loaded profile for {user_id}")
                    return profile
            
            # Create default
            default_profile = {
                "user_id": user_id,
                "created_at": datetime.utcnow().isoformat(),
                "subscription": "free",
                "email": None,
                "requests": [],
                "preferences": {},
            }
            
            self.logger.info(f"Created default profile for {user_id}")
            return default_profile
        
        except Exception as e:
            self.logger.error(f"Error loading profile {user_id}: {e}")
            return {"user_id": user_id, "subscription": "free", "error": str(e)}
    
    def update_user(self, user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update and persist profile"""
        try:
            profile = self.get_user(user_id)
            profile.update(updates)
            profile["updated_at"] = datetime.utcnow().isoformat()
            
            path = self._get_profile_path(user_id)
            
            # Write atomically
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(profile, f, indent=2, ensure_ascii=False)
            
            self.logger.debug(f"Updated profile for {user_id}")
            return profile
        
        except Exception as e:
            self.logger.error(f"Error updating profile {user_id}: {e}")
            raise
    
    def add_request(self, user_id: str, query: str, agent: str, result: Dict) -> None:
        """Track user request"""
        try:
            profile = self.get_user(user_id)
            
            profile.setdefault("requests", []).append({
                "query": query,
                "agent": agent,
                "timestamp": datetime.utcnow().isoformat(),
                "status": result.get("status", "unknown"),
            })
            
            # Keep only last 100 requests
            profile["requests"] = profile["requests"][-100:]
            
            self.update_user(user_id, profile)
        
        except Exception as e:
            self.logger.error(f"Error tracking request: {e}")
    
    def get_all_users(self) -> List[str]:
        """Get all user IDs"""
        return [f.stem for f in self.data_dir.glob("*.json")]
    
    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get user stats"""
        profile = self.get_user(user_id)
        requests = profile.get("requests", [])
        tasks = profile.get("task_history", [])
        job_applications = profile.get("job_applications", [])
        
        # Calculate task stats
        successful_tasks = sum(1 for task in tasks if task.get("success", False))
        total_execution_time = sum(task.get("execution_time", 0) for task in tasks)
        avg_response_time = total_execution_time / len(tasks) if tasks else 0
        
        return {
            "user_id": user_id,
            "total_requests": len(requests),
            "subscription": profile.get("subscription"),
            "created_at": profile.get("created_at"),
            "last_request": requests[-1] if requests else None,
            "agents_used": list(set(r.get("agent") for r in requests if r.get("agent"))),
            "last_activity": profile.get("last_activity"),
            "task_stats": {
                "total_tasks": len(tasks),
                "successful_tasks": successful_tasks,
                "avg_response_time": avg_response_time
            },
            "job_stats": {
                "total_applications": len(job_applications)
            }
        }
    
    def save_job_application(self, user_id: str, application_data: Dict[str, Any]) -> bool:
        """Save job application data"""
        try:
            profile = self.get_user(user_id)
            if "job_applications" not in profile:
                profile["job_applications"] = []
            profile["job_applications"].append(application_data)
            self.update_user(user_id, profile)
            return True
        except Exception as e:
            self.logger.error(f"Error saving job application: {e}")
            return False
    
    def log_user_activity(self, user_id: str, activity_type: str, details: str) -> bool:
        """Log user activity"""
        try:
            profile = self.get_user(user_id)
            if "activity_log" not in profile:
                profile["activity_log"] = []
            profile["activity_log"].append({
                "timestamp": datetime.utcnow().isoformat(),
                "type": activity_type,
                "details": details
            })
            # Keep only last 100 activities
            profile["activity_log"] = profile["activity_log"][-100:]
            
            # Update last_activity timestamp
            profile["last_activity"] = datetime.utcnow().isoformat()
            
            self.update_user(user_id, profile)
            return True
        except Exception as e:
            self.logger.error(f"Error logging user activity: {e}")
            return False
    
    def log_task_execution(self, user_id: str, agent_type: str, query: str, 
                          agent_name: str, success: bool, execution_time: float, 
                          result_summary: str = "") -> bool:
        """Log task execution"""
        try:
            profile = self.get_user(user_id)
            if "task_history" not in profile:
                profile["task_history"] = []
            
            task_data = {
                "agent_type": agent_type,
                "query": query,
                "agent_name": agent_name,
                "success": success,
                "execution_time": execution_time,
                "result_summary": result_summary,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            profile["task_history"].append(task_data)
            # Keep only last 100 tasks
            profile["task_history"] = profile["task_history"][-100:]
            self.update_user(user_id, profile)
            return True
        except Exception as e:
            self.logger.error(f"Error logging task execution: {e}")
            return False
    
    def get_profile(self, user_id: str) -> Dict[str, Any]:
        """Alias for get_user for backward compatibility"""
        return self.get_user(user_id)

# Global instance
profile_manager = UserProfileManager()
