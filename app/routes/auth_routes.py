from fastapi import APIRouter, HTTPException, Depends, Header
from sqlalchemy.orm import Session
from app.database.session import SessionLocal
from app.database.models import User
import bcrypt
from jose import jwt
from pydantic import BaseModel
import os
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


class PasswordResetRequest(BaseModel):
  email: str


class PasswordResetConfirm(BaseModel):
  token: str
  new_password: str


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


def create_reset_token(user_id: int):
  """Short-lived reset token (1 hour)"""
  payload = {
    "user_id": user_id,
    "type": "reset",
    "exp": datetime.utcnow() + timedelta(hours=1),
  }
  return jwt.encode(payload, SECRET, algorithm=ALGORITHM)


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
# REQUEST PASSWORD RESET
# -----------------------------
@router.post("/request-password-reset")
def request_password_reset(data: PasswordResetRequest, db: Session = Depends(get_db)):
  """
  1) User submits email
  2) If user exists -> create reset token
  3) For now: return token in response + log it (later: send via email)
  """
  user = db.query(User).filter(User.email == data.email).first()

  # Always return success-style message (don't leak which emails exist)
  if not user:
    return {
      "message": "If an account with this email exists, a reset link has been prepared."
    }

  reset_token = create_reset_token(user.id)

  # For now we just LOG it so you can see it in Render logs
  print("🔑 PASSWORD RESET TOKEN FOR USER", user.id, ":", reset_token)

  # And also return it in response so you can test easily
  return {
    "message": "If an account with this email exists, a reset link has been prepared.",
    "reset_token": reset_token,
  }


# -----------------------------
# RESET PASSWORD
# -----------------------------
@router.post("/reset-password")
def reset_password(data: PasswordResetConfirm, db: Session = Depends(get_db)):
  """
  1) Frontend sends token + new_password
  2) We decode token, verify it's a reset token and not expired
  3) Update user password
  """
  try:
    payload = jwt.decode(data.token, SECRET, algorithms=[ALGORITHM])
  except Exception:
    raise HTTPException(status_code=400, detail="Invalid or expired token")

  if payload.get("type") != "reset":
    raise HTTPException(status_code=400, detail="Invalid reset token")

  user_id = payload.get("user_id")
  if not user_id:
    raise HTTPException(status_code=400, detail="Invalid reset token payload")

  user = db.query(User).filter(User.id == user_id).first()
  if not user:
    raise HTTPException(status_code=404, detail="User not found")

  # Update password
  hashed_pw = bcrypt.hashpw(data.new_password.encode(), bcrypt.gensalt()).decode()
  user.password = hashed_pw
  db.commit()

  return {"message": "Password has been reset successfully."}
