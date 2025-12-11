"""
Database layer for AI Agent Platform
Persistent storage with SQLite
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import threading

class DatabaseManager:
    def __init__(self, db_path: str = "data/agent_platform.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self._local = threading.local()
        self.init_db()

    @property
    def conn(self):
        if not hasattr(self._local, 'conn'):
            self._local.conn = sqlite3.connect(self.db_path)
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn

    def init_db(self):
        """Initialize database tables"""
        with self.conn:
            # Users table
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT,
                    subscription_tier TEXT DEFAULT 'free',
                    tasks_used INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Tasks table
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    query TEXT NOT NULL,
                    agent TEXT NOT NULL,
                    result TEXT,  -- JSON
                    execution_time REAL,
                    status TEXT DEFAULT 'pending',
                    error TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')

            # User profiles table
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS user_profiles (
                    user_id TEXT PRIMARY KEY,
                    profile_data TEXT,  -- JSON
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')

            # API usage tracking
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS api_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    endpoint TEXT,
                    tokens_used INTEGER DEFAULT 0,
                    cost REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')

    def create_user(self, user_id: str, email: str, subscription_tier: str = "free") -> bool:
        """Create a new user"""
        try:
            with self.conn:
                self.conn.execute(
                    "INSERT INTO users (id, email, subscription_tier) VALUES (?, ?, ?)",
                    (user_id, email, subscription_tier)
                )
            return True
        except sqlite3.IntegrityError:
            return False

    def get_user(self, user_id: str) -> Optional[Dict]:
        """Get user by ID"""
        cursor = self.conn.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        cursor = self.conn.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def update_user_tasks(self, user_id: str, tasks_used: int):
        """Update user's task count"""
        with self.conn:
            self.conn.execute(
                "UPDATE users SET tasks_used = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (tasks_used, user_id)
            )

    def save_task(self, task_data: Dict):
        """Save task execution result"""
        with self.conn:
            self.conn.execute(
                """INSERT INTO tasks
                   (task_id, user_id, query, agent, result, execution_time, status, error)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    task_data["task_id"],
                    task_data.get("user_id"),
                    task_data["query"],
                    task_data["agent"],
                    json.dumps(task_data.get("result")),
                    task_data["execution_time"],
                    task_data.get("status", "success"),
                    task_data.get("error")
                )
            )

    def get_user_tasks(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get recent tasks for user"""
        cursor = self.conn.execute(
            "SELECT * FROM tasks WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit)
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_all_tasks(self, limit: int = 100) -> List[Dict]:
        """Get all tasks (admin)"""
        cursor = self.conn.execute(
            "SELECT * FROM tasks ORDER BY created_at DESC LIMIT ?",
            (limit,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def save_user_profile(self, user_id: str, profile_data: Dict):
        """Save user profile data"""
        with self.conn:
            self.conn.execute(
                """INSERT OR REPLACE INTO user_profiles
                   (user_id, profile_data, updated_at)
                   VALUES (?, ?, CURRENT_TIMESTAMP)""",
                (user_id, json.dumps(profile_data))
            )

    def get_user_profile(self, user_id: str) -> Optional[Dict]:
        """Get user profile"""
        cursor = self.conn.execute(
            "SELECT profile_data FROM user_profiles WHERE user_id = ?",
            (user_id,)
        )
        row = cursor.fetchone()
        if row:
            return json.loads(row[0])
        return None

    def log_api_usage(self, user_id: str, endpoint: str, tokens: int = 0, cost: float = 0.0):
        """Log API usage for billing"""
        with self.conn:
            self.conn.execute(
                "INSERT INTO api_usage (user_id, endpoint, tokens_used, cost) VALUES (?, ?, ?, ?)",
                (user_id, endpoint, tokens, cost)
            )

    def get_stats(self) -> Dict:
        """Get platform statistics"""
        stats = {}

        # User stats
        cursor = self.conn.execute("SELECT COUNT(*) as count FROM users")
        stats["total_users"] = cursor.fetchone()[0]

        # Task stats
        cursor = self.conn.execute("SELECT COUNT(*) as count FROM tasks")
        stats["total_tasks"] = cursor.fetchone()[0]

        # Recent tasks
        cursor = self.conn.execute(
            "SELECT COUNT(*) as count FROM tasks WHERE created_at >= datetime('now', '-24 hours')"
        )
        stats["tasks_last_24h"] = cursor.fetchone()[0]

        # Agent usage
        cursor = self.conn.execute(
            "SELECT agent, COUNT(*) as count FROM tasks GROUP BY agent ORDER BY count DESC"
        )
        stats["agent_usage"] = [dict(row) for row in cursor.fetchall()]

        return stats

    def close(self):
        """Close database connection"""
        if hasattr(self._local, 'conn'):
            self._local.conn.close()

# Global database instance
db = DatabaseManager()