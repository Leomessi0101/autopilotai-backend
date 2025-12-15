from fastapi import APIRouter, HTTPException, Depends, Header
from sqlalchemy.orm import Session
from app.database.session import SessionLocal
from app.database.models import User
import bcrypt
from jose import jwt
from pydantic import BaseModel

SECRET = "supersecretkey"
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


# -----------------------------
# /me  (Used by Dashboard)
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
        "remaining_generations": None if user.monthly_limit is None else max(0, user.monthly_limit - user.used_generations),
        "last_reset": user.last_reset
    }
