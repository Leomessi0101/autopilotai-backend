from fastapi import APIRouter, HTTPException, Depends, Header
from sqlalchemy.orm import Session
from app.database.session import SessionLocal
from app.database.models import User
import bcrypt
from jose import jwt
from pydantic import BaseModel
import os
import requests
import secrets
from datetime import datetime, timedelta

# -----------------------------
# JWT CONFIG (SINGLE SOURCE OF TRUTH)
# -----------------------------
SECRET = os.getenv("JWT_SECRET", "supersecretkey")
ALGORITHM = "HS256"

router = APIRouter()

# -----------------------------
# Request Models
# -----------------------------
class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


# -----------------------------
# DB Dependency
# -----------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -----------------------------
# JWT Creation
# -----------------------------
def create_access_token(user_id: int):
    return jwt.encode({"user_id": user_id}, SECRET, algorithm=ALGORITHM)


# -----------------------------
# REGISTER
# -----------------------------
@router.post("/register")
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode()

    new_user = User(
        name=data.name,
        email=data.email,
        password=hashed_pw,
        subscription_plan="Free",
        monthly_limit=10,
        used_generations=0,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "Account created", "user_id": new_user.id}


# -----------------------------
# LOGIN
# -----------------------------
@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    if not bcrypt.checkpw(data.password.encode(), user.password.encode()):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    token = create_access_token(user.id)

    return {
        "token": token,
        "subscription_plan": user.subscription_plan,
        "monthly_limit": user.monthly_limit,
        "used_generations": user.used_generations,
    }


# -----------------------------
# /me
# -----------------------------
@router.get("/me")
def me(Authorization: str = Header(None), db: Session = Depends(get_db)):
    if Authorization is None:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    token = Authorization.replace("Bearer ", "")

    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
        user_id = payload["user_id"]
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "name": user.name,
        "email": user.email,
        "subscription": user.subscription_plan,
        "used_generations": user.used_generations,
        "monthly_limit": user.monthly_limit,
        "remaining_generations": None
        if user.monthly_limit is None
        else max(0, user.monthly_limit - user.used_generations),
        "last_reset": user.last_reset,
    }


# -----------------------------
# FORGOT PASSWORD
# -----------------------------
@router.post("/forgot-password")
def forgot_password(data: dict, db: Session = Depends(get_db)):
    email = data.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email required")

    user = db.query(User).filter(User.email == email).first()

    # Always return OK (don't reveal if user exists)
    if not user:
        return {"message": "If an account exists, a reset link has been sent."}

    # Generate secure token
    token = secrets.token_urlsafe(48)

    user.reset_token = token
    user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
    db.commit()

    frontend_url = os.getenv("FRONTEND_URL", "https://www.autopilotai.dev")
    reset_link = f"{frontend_url}/reset-password?token={token}"

    # Send email via Resend
    try:
        resend_api_key = os.getenv("RESEND_API_KEY")
        email_from = os.getenv("EMAIL_FROM", "noreply@autopilotai.dev")

        if resend_api_key:
            headers = {
                "Authorization": f"Bearer {resend_api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "from": email_from,
                "to": email,
                "subject": "Reset your AutopilotAI password",
                "html": f"""
                <h2>Reset Your Password</h2>
                <p>We received a request to reset your AutopilotAI password.</p>
                <p>Click the button below to choose a new password:</p>
                <p>
                  <a href="{reset_link}" style="
                    background:black;
                    padding:12px 18px;
                    color:white;
                    border-radius:8px;
                    text-decoration:none;
                    display:inline-block;
                  ">
                    Reset Password
                  </a>
                </p>
                <p>If you did not request this, you can safely ignore this email.</p>
                <p style="font-size:12px;color:#888;">This link expires in 1 hour.</p>
                """,
            }

            requests.post("https://api.resend.com/emails", json=payload, headers=headers)
        else:
            print("⚠️ RESEND_API_KEY not set – cannot send reset email.")

    except Exception as e:
        print("EMAIL ERROR:", e)

    return {"message": "If an account exists, a reset link has been sent."}


# -----------------------------
# RESET PASSWORD
# -----------------------------
@router.post("/reset-password")
def reset_password(data: dict, db: Session = Depends(get_db)):
    token = data.get("token")
    new_password = data.get("password")

    if not token or not new_password:
        raise HTTPException(status_code=400, detail="Missing token or password")

    user = db.query(User).filter(User.reset_token == token).first()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    if not user.reset_token_expires or user.reset_token_expires < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Token expired")

    hashed_pw = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    user.password = hashed_pw
    user.reset_token = None
    user.reset_token_expires = None

    db.commit()

    return {"message": "Password updated successfully"}
