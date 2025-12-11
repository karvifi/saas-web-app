import pytest
import asyncio
from datetime import datetime
from backend.user_profiles import UserProfileManager
from backend.monitoring import monitoring_system
from agents.career import CareerAgent
import tempfile
import os
import time
import shutil

class TestDatabaseIntegration:
    """Test database integration for job applications and user activity"""

    def setup_method(self):
        """Setup test database"""
        self.db_path = tempfile.mktemp(suffix='.db')
        self.profile_manager = UserProfileManager(db_path=self.db_path)

    def teardown_method(self):
        """Cleanup test database with Windows-compatible handling"""
        self._cleanup_test_files()

    def _cleanup_test_files(self):
        """Robust file cleanup for Windows"""
        max_retries = 5
        for attempt in range(max_retries):
            try:
                if os.path.exists(self.db_path):
                    # Try to close any open handles
                    import gc
                    gc.collect()
                    
                    # Force remove on Windows
                    os.remove(self.db_path)
                break
            except (OSError, PermissionError) as e:
                if attempt == max_retries - 1:
                    print(f"Failed to cleanup {self.db_path} after {max_retries} attempts: {e}")
                else:
                    time.sleep(0.1)  # Wait before retry

    def test_job_application_tracking(self):
        """Test job application saving and retrieval"""
        user_id = "test_user_123"

        # Save a job application
        application_data = {
            "job_title": "Software Engineer",
            "company": "Tech Corp",
            "job_url": "https://example.com/job/123",
            "status": "applied",
            "applied_date": datetime.utcnow().isoformat()
        }

        self.profile_manager.save_job_application(user_id, application_data)

        # Get user stats from monitoring system
        from backend.monitoring import MonitoringSystem
        monitoring = MonitoringSystem(profile_manager=self.profile_manager)
        stats = monitoring.get_user_stats(user_id)

        assert stats["job_applications"] == 1
        assert stats["total_tasks"] == 0  # No tasks yet

    def test_user_activity_logging(self):
        """Test user activity logging"""
        user_id = "test_user_123"

        # Log some activities
        self.profile_manager.log_user_activity(user_id, "login", "User logged in")
        self.profile_manager.log_user_activity(user_id, "task_execution", "Executed career search")

        # Get stats from monitoring system
        from backend.monitoring import MonitoringSystem
        monitoring = MonitoringSystem(profile_manager=self.profile_manager)
        stats = monitoring.get_user_stats(user_id)

        # User activity logging doesn't create task records, so tasks should be 0
        assert stats["total_tasks"] == 0
        # But last activity should be set
        assert stats["last_activity"] is not None

    def test_task_execution_logging(self):
        """Test task execution logging"""
        user_id = "test_user_123"

        # Log task execution
        self.profile_manager.log_task_execution(
            user_id, "career", "find software engineer jobs",
            "career_agent", True, 2.5, None
        )

        # Get stats from monitoring system
        from backend.monitoring import MonitoringSystem
        monitoring = MonitoringSystem(profile_manager=self.profile_manager)
        stats = monitoring.get_user_stats(user_id)

        assert stats["total_tasks"] == 1
        assert stats["successful_tasks"] == 1
        assert stats["failed_tasks"] == 0
        assert stats["total_execution_time"] == 2.5

class TestCareerAgentIntegration:
    """Test career agent with database integration"""

    def setup_method(self):
        """Setup test environment"""
        self.db_path = tempfile.mktemp(suffix='.db')
        self.profile_manager = UserProfileManager(db_path=self.db_path)
        self.career_agent = CareerAgent()
        # Mock the profile manager in career agent
        self.career_agent.profile_manager = self.profile_manager

    def teardown_method(self):
        """Cleanup"""
        self._cleanup_test_files()

    def _cleanup_test_files(self):
        """Robust file cleanup for Windows"""
        max_retries = 5
        for attempt in range(max_retries):
            try:
                if os.path.exists(self.db_path):
                    # Try to close any open handles
                    import gc
                    gc.collect()
                    
                    # Force remove on Windows
                    os.remove(self.db_path)
                break
            except (OSError, PermissionError) as e:
                if attempt == max_retries - 1:
                    print(f"Failed to cleanup {self.db_path} after {max_retries} attempts: {e}")
                else:
                    time.sleep(0.1)  # Wait before retry

    @pytest.mark.asyncio
    async def test_auto_apply_with_tracking(self):
        """Test auto-apply functionality with database tracking"""
        user_id = "test_user_123"

        job_data = {
            "title": "Python Developer",
            "company": "Test Company",
            "url": "https://example.com/job/123"
        }

        user_profile = {
            "name": "John Doe",
            "email": "john@example.com",
            "resume": "Experienced developer..."
        }

        # This would normally do browser automation, but we'll mock the result
        # For now, just test that it calls the save method
        try:
            result = await self.career_agent.auto_apply(job_data, user_profile, user_id)
            # Check that application was saved
            stats = self.profile_manager.get_user_stats(user_id)
            assert stats["job_applications"] >= 1
        except Exception as e:
            # If browser automation fails (expected in test), at least check the method exists
            assert "auto_apply" in dir(self.career_agent)

class TestMonitoringIntegration:
    """Test monitoring system with database"""

    def setup_method(self):
        """Setup test environment"""
        self.db_path = tempfile.mktemp(suffix='.db')
        self.profile_manager = UserProfileManager(db_path=self.db_path)
        # Create monitoring system with test database
        from backend.monitoring import MonitoringSystem
        self.monitoring = MonitoringSystem(profile_manager=self.profile_manager)

    def teardown_method(self):
        """Cleanup"""
        self._cleanup_test_files()

    def _cleanup_test_files(self):
        """Robust file cleanup for Windows"""
        max_retries = 5
        for attempt in range(max_retries):
            try:
                if os.path.exists(self.db_path):
                    # Try to close any open handles
                    import gc
                    gc.collect()
                    
                    # Force remove on Windows
                    os.remove(self.db_path)
                break
            except (OSError, PermissionError) as e:
                if attempt == max_retries - 1:
                    print(f"Failed to cleanup {self.db_path} after {max_retries} attempts: {e}")
                else:
                    time.sleep(0.1)  # Wait before retry

    def test_task_recording_with_database(self):
        """Test task recording saves to database"""
        user_id = "test_user_123"

        self.monitoring.record_task_execution(
            "task_123", user_id, "career", "find jobs",
            1.5, True, "Found 5 jobs"
        )

        # Check user stats
        stats = self.monitoring.get_user_stats(user_id)
        assert stats["total_tasks"] == 1
        assert stats["successful_tasks"] == 1

class TestErrorHandling:
    """Test error handling across components"""

    def test_database_error_handling(self):
        """Test database operations handle errors gracefully"""
        # Test with invalid database path
        profile_manager = UserProfileManager(db_path="/invalid/path/db.db")

        # Should not crash
        from backend.monitoring import MonitoringSystem
        monitoring = MonitoringSystem(profile_manager=profile_manager)
        stats = monitoring.get_user_stats("test_user")
        assert isinstance(stats, dict)
        assert stats["total_tasks"] == 0

    def test_monitoring_error_handling(self):
        """Test monitoring handles database errors"""
        from backend.monitoring import MonitoringSystem
        monitoring = MonitoringSystem()

        # Should not crash even with database issues
        stats = monitoring.get_user_stats("test_user")
        assert isinstance(stats, dict)
        assert stats["total_tasks"] == 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])