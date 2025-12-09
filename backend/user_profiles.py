"""
User Profile System - Personalization & Context Memory
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import os
from loguru import logger

class UserProfileManager:
    """
    Manages user profiles, preferences, and context
    """
    
    def __init__(self, storage_path: str = "data/user_profiles"):
        self.storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)
    
    def create_profile(self, user_id: str, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new user profile"""
        
        profile = {
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "personal_info": {
                "first_name": profile_data.get("first_name", ""),
                "last_name": profile_data.get("last_name", ""),
                "email": profile_data.get("email", ""),
                "phone": profile_data.get("phone", "")
            },
            "professional": {
                "title": profile_data.get("job_title", ""),
                "skills": profile_data.get("skills", []),
                "experience_years": profile_data.get("experience_years", 0),
                "preferred_locations": profile_data.get("preferred_locations", []),
                "salary_expectation": profile_data.get("salary_expectation", 0)
            },
            "preferences": {
                "search_language": "en",
                "timezone": "UTC",
                "notification_settings": {
                    "email": True,
                    "push": False
                }
            },
            "context": {
                "recent_queries": [],
                "favorite_searches": [],
                "blocked_domains": []
            },
            "statistics": {
                "total_queries": 0,
                "successful_tasks": 0,
                "failed_tasks": 0,
                "average_response_time": 0.0
            }
        }
        
        self.save_profile(user_id, profile)
        logger.info(f"✅ Profile created for user: {user_id}")
        
        return profile
    
    def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Load user profile"""
        profile_file = os.path.join(self.storage_path, f"{user_id}.json")
        
        if os.path.exists(profile_file):
            with open(profile_file, 'r') as f:
                return json.load(f)
        
        return None
    
    def save_profile(self, user_id: str, profile: Dict[str, Any]):
        """Save user profile"""
        profile['updated_at'] = datetime.utcnow().isoformat()
        profile_file = os.path.join(self.storage_path, f"{user_id}.json")
        
        with open(profile_file, 'w') as f:
            json.dump(profile, f, indent=2)
    
    def update_context(self, user_id: str, query: str, result: Any):
        """Update user context with new query"""
        profile = self.get_profile(user_id)
        
        if profile:
            # Add to recent queries
            profile['context']['recent_queries'].insert(0, {
                "query": query,
                "timestamp": datetime.utcnow().isoformat(),
                "success": result.get('status') == 'success'
            })
            
            # Keep only last 50 queries
            profile['context']['recent_queries'] = profile['context']['recent_queries'][:50]
            
            # Update statistics
            profile['statistics']['total_queries'] += 1
            if result.get('status') == 'success':
                profile['statistics']['successful_tasks'] += 1
            else:
                profile['statistics']['failed_tasks'] += 1
            
            self.save_profile(user_id, profile)
    
    def get_personalized_context(self, user_id: str) -> Dict[str, Any]:
        """Get context for personalized responses"""
        profile = self.get_profile(user_id)
        
        if not profile:
            return {}
        
        return {
            "user_skills": profile['professional']['skills'],
            "location": profile['personal_info']['location'],
            "recent_interests": [q['query'] for q in profile['context']['recent_queries'][:5]],
            "preferences": profile['preferences']
        }

# Global instance
profile_manager = UserProfileManager()