from fastapi import APIRouter, HTTPException, Depends, Header
from sqlalchemy.orm import Session
from app.database.session import SessionLocal
from app.database.models import User
import bcrypt
from jose import jwt
from pydantic import BaseModel
import os
from datetime import datetime, timedelta
import uuid
import resend

# -----------------------------
# JWT CONFIG
# -----------------------------
SECRET = os.getenv("JWT_SECRET", "supersecretkey")
ALGORITHM = "HS256"

# -----------------------------
# RESEND CONFIG
# -----------------------------
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
resend.api_key = RESEND_API_KEY

FRONTEND_URL = os.getenv("FRONTEND_URL", "https://www.autopilotai.dev")

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

class ResetPasswordRequest(BaseModel):
    token: str
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
# JWT
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
        used_generations=0
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

    if not user or not bcrypt.checkpw(data.password.encode(), user.password.encode()):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    token = create_access_token(user.id)

    return {
        "token": token,
        "subscription_plan": user.subscription_plan,
        "monthly_limit": user.monthly_limit,
        "used_generations": user.used_generations
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


# -----------------------------
# FORGOT PASSWORD
# -----------------------------
@router.post("/forgot-password")
def forgot_password(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()

    # Do NOT reveal if user doesn't exist (security best practice)
    if not user:
        return {"message": "If that email exists, a reset link was sent."}

    token = str(uuid.uuid4())
    user.reset_token = token
    user.reset_token_expires = datetime.utcnow() + timedelta(minutes=30)

    db.commit()

    reset_link = f"{FRONTEND_URL}/reset-password?token={token}"

    try:
        resend.Emails.send({
            "from": "AutopilotAI <support@autopilotai.dev>",
            "to": user.email,
            "subject": "Reset your AutopilotAI password",
            "html": f"""
                <h2>Reset your password</h2>
                <p>Click the button below to create a new password.</p>
                <a href="{reset_link}"
                   style="padding:12px 18px;
                          background:#000;
                          color:#fff;
                          text-decoration:none;
                          border-radius:8px;">
                   Reset Password
                </a>
                <p>Or copy this link:<br>{reset_link}</p>
                <p>This link expires in 30 minutes.</p>
            """
        })
    except Exception as e:
        print("EMAIL ERROR:", e)
        raise HTTPException(500, "Failed to send email")

    return {"message": "Reset email sent"}


# -----------------------------
# RESET PASSWORD
# -----------------------------
@router.post("/reset-password")
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.reset_token == data.token).first()

    if not user:
        raise HTTPException(400, "Invalid token")

    if not user.reset_token_expires or user.reset_token_expires < datetime.utcnow():
        raise HTTPException(400, "Token expired")

    hashed_pw = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode()

    user.password = hashed_pw
    user.reset_token = None
    user.reset_token_expires = None

    db.commit()

    return {"message": "Password reset successful"}
