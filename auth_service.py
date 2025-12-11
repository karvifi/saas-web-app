"""
Authentication service for AI Agent Platform
JWT-based authentication with proper security
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
import bcrypt
import secrets
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from database import db

# Configuration
SECRET_KEY = "your-secret-key-change-in-production"  # Load from env
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

security = HTTPBearer(auto_error=False)

class UserCreate(BaseModel):
    email: str
    password: str
    first_name: str = ""
    last_name: str = ""

class UserLogin(BaseModel):
    email: str
    password: str

class TokenData(BaseModel):
    user_id: str
    email: str

class AuthService:
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None):
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def verify_token(token: str) -> Optional[TokenData]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: str = payload.get("sub")
            email: str = payload.get("email")
            if user_id is None:
                return None
            return TokenData(user_id=user_id, email=email)
        except jwt.PyJWTError:
            return None

    @staticmethod
    def generate_user_id() -> str:
        """Generate unique user ID"""
        return f"user_{secrets.token_hex(8)}"

    async def register_user(self, user_data: UserCreate) -> Dict[str, Any]:
        """Register a new user"""
        # Check if user already exists
        existing_user = db.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")

        # Create new user
        user_id = self.generate_user_id()
        hashed_password = self.hash_password(user_data.password)

        # Save to database
        success = db.create_user(user_id, user_data.email)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to create user")

        # Update with password (in real app, store separately)
        # For now, we'll store in the user record
        with db.conn:
            db.conn.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (hashed_password, user_id)
            )

        # Create access token
        access_token = self.create_access_token(
            data={"sub": user_id, "email": user_data.email}
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user_id,
                "email": user_data.email,
                "subscription_tier": "free"
            }
        }

    async def authenticate_user(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticate user login"""
        user = db.get_user_by_email(email)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        if not self.verify_password(password, user.get("password_hash", "")):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        # Create access token
        access_token = self.create_access_token(
            data={"sub": user["id"], "email": user["email"]}
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user["id"],
                "email": user["email"],
                "subscription_tier": user["subscription_tier"]
            }
        }

    async def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(security)):
        """Get current authenticated user"""
        if not credentials:
            raise HTTPException(status_code=401, detail="Not authenticated")

        token_data = self.verify_token(credentials.credentials)
        if not token_data:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        user = db.get_user(token_data.user_id)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        return user

    async def get_current_user_optional(self, credentials: HTTPAuthorizationCredentials = Depends(security)):
        """Get current user if authenticated, otherwise return None"""
        if not credentials:
            return None

        token_data = self.verify_token(credentials.credentials)
        if not token_data:
            return None

        return db.get_user(token_data.user_id)

# Global auth service instance
auth_service = AuthService()