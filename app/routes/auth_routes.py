from fastapi import APIRouter, HTTPException, Depends, Header, Request
from sqlalchemy.orm import Session
from app.database.session import SessionLocal
from app.database.models import User
import bcrypt
from jose import jwt, JWTError
from pydantic import BaseModel
import os
from datetime import datetime, timedelta
import requests


# -----------------------------
# JWT CONFIG
# -----------------------------
SECRET = os.getenv("JWT_SECRET", "supersecretkey")
ALGORITHM = "HS256"

router = APIRouter()

# -----------------------------
# RESET TOKEN CONFIG
# -----------------------------
RESET_SECRET = os.getenv("RESET_TOKEN_SECRET", "resetsecret")
RESET_EXP_MINUTES = 30

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

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


# =============================
# DATABASE SESSION
# =============================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =============================
# JWT CREATION
# =============================
def create_access_token(user_id: int):
    return jwt.encode({"user_id": user_id}, SECRET, algorithm=ALGORITHM)


# =============================
# REGISTER
# =============================
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
        used_generations=0
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "Account created", "user_id": new_user.id}


# =============================
# LOGIN
# =============================
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
        "used_generations": user.used_generations
    }


# =============================
# /me
# =============================
@router.get("/me")
def me(Authorization: str = Header(None), db: Session = Depends(get_db)):
    if Authorization is None:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    token = Authorization.replace("Bearer ", "")

    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
        user_id = payload["user_id"]
    except:
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
        "last_reset": user.last_reset
    }



# =================================================================
# ================== PASSWORD RESET SYSTEM =========================
# =================================================================


# -----------------------------
# REQUEST RESET
# -----------------------------
@router.post("/request-password-reset")
def request_password_reset(email: str, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.email == email).first()

    # Always respond success (security best practice)
    if not user:
        return {"message": "If an account exists, a reset link has been sent."}

    token = jwt.encode(
        {
            "user_id": user.id,
            "exp": datetime.utcnow() + timedelta(minutes=RESET_EXP_MINUTES),
        },
        RESET_SECRET,
        algorithm="HS256"
    )

    reset_link = f"{FRONTEND_URL}/reset-password?token={token}"

    # ----- SEND EMAIL VIA RESEND -----
    try:
        headers = {
            "Authorization": f"Bearer {os.getenv('RESEND_API_KEY')}",
            "Content-Type": "application/json"
        }

        data = {
            "from": "AutopilotAI <no-reply@autopilotai.dev>",
            "to": [email],
            "subject": "Reset your AutopilotAI password",
            "html": f"""
            <h2>Password Reset</h2>
            <p>Click below to reset your password.</p>
            <a href="{reset_link}"
            style="padding:12px 20px;background:black;color:white;border-radius:8px;text-decoration:none;">
                Reset Password
            </a>
            <p>This link expires in 30 minutes.</p>
            """
        }

        requests.post("https://api.resend.com/emails", headers=headers, json=data)

    except Exception as e:
        print("RESEND ERROR:", e)

    return {"message": "If an account exists, a reset link has been sent."}


# -----------------------------
# SUBMIT NEW PASSWORD
# -----------------------------
class ResetPasswordModel(BaseModel):
    token: str
    new_password: str


@router.post("/reset-password")
def reset_password(data: ResetPasswordModel, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(data.token, RESET_SECRET, algorithms=["HS256"])
        user_id = payload.get("user_id")
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired reset link")

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    hashed_pw = bcrypt.hashpw(data.new_password.encode(), bcrypt.gensalt()).decode()
    user.password = hashed_pw

    db.commit()

    return {"message": "Password reset successful"}
