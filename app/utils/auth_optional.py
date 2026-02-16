"""
Optional authentication utilities
"""

from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthCredential
from typing import Optional
import jwt
from app.database.models import User
from app.database.session import SessionLocal
import os

security = HTTPBearer(auto_error=False)

def get_current_user_optional(credential: Optional[HTTPAuthCredential] = Depends(security)) -> Optional[User]:
    """
    Get current user from JWT token, but don't fail if no token provided
    Returns None if no valid token
    """
    if not credential:
        return None
    
    try:
        token = credential.credentials
        secret = os.getenv("SECRET_KEY", "your-secret-key-change-this")
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        user_id = payload.get("user_id")
        
        if not user_id:
            return None
        
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            return user
        finally:
            db.close()
    except:
        return None