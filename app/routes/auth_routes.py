from fastapi import APIRouter, HTTPException, Depends, Header
from sqlalchemy.orm import Session
from app.database.session import SessionLocal
from app.database.models import User
import bcrypt
from jose import jwt
from pydantic import BaseModel, EmailStr
import os
from datetime import datetime, timedelta
import resend

from app.utils.usage import get_user_limit   # ✅ IMPORTANT

SECRET = os.getenv("JWT_SECRET", "supersecretkey")
ALGORITHM = "HS256"

router = APIRouter()


# ========================= MODELS =========================
class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


# ========================= DB =========================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ========================= JWT =========================
def create_access_token(user_id: int):
    return jwt.encode({"user_id": user_id}, SECRET, algorithm=ALGORITHM)


# ========================= REGISTER =========================
@router.post("/register")
def register(data: RegisterRequest, db: Session = Depends(get_db)):

    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(400, "Email already registered")

    hashed_pw = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode()

    new_user = User(
        name=data.name,
        email=data.email,
        password=hashed_pw,
        subscription_plan="free",     # ✅ lowercase ALWAYS
        monthly_limit=10,
        used_generations=0
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "Account created"}


# ========================= LOGIN =========================
@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.email == data.email).first()

    if not user:
        raise HTTPException(400, "Invalid credentials")

    if not bcrypt.checkpw(data.password.encode(), user.password.encode()):
        raise HTTPException(400, "Invalid credentials")

    token = create_access_token(user.id)

    limit = get_user_limit(user.subscription_plan)
    return {
        "token": token,
        "subscription_plan": user.subscription_plan,
        "monthly_limit": limit,
        "used_generations": user.used_generations,
    }


# ========================= ME =========================
@router.get("/me")
def me(Authorization: str = Header(None), db: Session = Depends(get_db)):

    if not Authorization:
        raise HTTPException(401, "Missing Authorization header")

    token = Authorization.replace("Bearer ", "")

    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
        user_id = payload["user_id"]
    except:
        raise HTTPException(401, "Invalid token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    # ✅ ALWAYS compute real monthly limit
    limit = get_user_limit(user.subscription_plan)

    remaining = None
    if limit is not None:
        remaining = max(limit - (user.used_generations or 0), 0)

    return {
        "name": user.name,
        "email": user.email,
        "subscription": user.subscription_plan,
        "used_generations": user.used_generations,
        "monthly_limit": limit,
        "remaining_generations": remaining,
        "last_reset": user.last_reset,
    }


# ========================= FORGOT PASSWORD =========================
@router.post("/forgot-password")
def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.email == data.email).first()

    # Security: Always respond ok
    if not user:
        return {"message": "If email exists, reset link sent."}

    token_payload = {
        "user_id": user.id,
        "exp": datetime.utcnow() + timedelta(minutes=30)
    }

    reset_token = jwt.encode(token_payload, SECRET, algorithm=ALGORITHM)

    user.reset_token = reset_token
    user.reset_token_expires = datetime.utcnow() + timedelta(minutes=30)
    db.commit()

    resend.api_key = os.getenv("RESEND_API_KEY")

    reset_url = f"https://www.autopilotai.dev/reset-password?token={reset_token}"

    resend.Emails.send({
        "from": os.getenv("EMAIL_FROM", "support@autopilotai.dev"),
        "to": user.email,
        "subject": "Reset your AutopilotAI Password",
        "html": f"""
        <h2>Password Reset</h2>
        <p>Click below to reset your password:</p>
        <a href="{reset_url}">{reset_url}</a>
        """
    })

    return {"message": "Reset email sent"}


# ========================= RESET PASSWORD =========================
@router.post("/reset-password")
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):

    try:
        payload = jwt.decode(data.token, SECRET, algorithms=[ALGORITHM])
        user_id = payload["user_id"]
    except:
        raise HTTPException(400, "Invalid or expired reset token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    if user.reset_token != data.token:
        raise HTTPException(400, "Token mismatch")

    if user.reset_token_expires < datetime.utcnow():
        raise HTTPException(400, "Token expired")

    hashed_pw = bcrypt.hashpw(data.new_password.encode(), bcrypt.gensalt()).decode()
    user.password = hashed_pw
    user.reset_token = None
    user.reset_token_expires = None

    db.commit()

    return {"message": "Password updated successfully"}
