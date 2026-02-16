from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session
from jose import jwt
from typing import Optional
import os

from app.database.session import SessionLocal
from app.database.models import User

SECRET = os.getenv("JWT_SECRET", "supersecretkey")
ALGORITHM = "HS256"


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    Authorization: str = Header(None),
    db: Session = Depends(get_db),
):
    """Get authenticated user (required)"""
    if not Authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    token = Authorization.replace("Bearer ", "")

    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.id == user_id).first()

    # 🔥 DEV MODE: FORCE USER EXISTS
    if not user:
        user = User(
            id=user_id,
            email="dev@local",
            name="Dev User",
            subscription_plan="pro",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    return user


def get_current_user_optional(
    Authorization: str = Header(None),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Get current user from JWT token, but don't fail if no token provided"""
    if not Authorization:
        return None

    token = Authorization.replace("Bearer ", "")

    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        
        if not user_id:
            return None
            
        user = db.query(User).filter(User.id == user_id).first()
        return user
    except Exception:
        return None