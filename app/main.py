from dotenv import load_dotenv
load_dotenv()

import os
print("PRICE_GROWTH FROM ENV:", os.getenv("PRICE_GROWTH"))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Database
from app.database.session import engine
from app.database.models import Base

# Routers
from app.routes.profile_routes import router as profile_router
from app.routes.usage_routes import router as usage_router
from app.routes.stripe_routes import router as stripe_router
from app.routes.auth_routes import router as auth_router
from app.ai.content_routes import router as content_router
from app.ai.email_routes import router as email_router
from app.routes.content_history import router as history_router
from app.ai.ads_routes import router as ads_router
from app.routes.dashboard_routes import router as dashboard_router
from app.routes.work_routes import router as work_router

import sys
print(">>> Python executable:", sys.executable)

# -------------------- APP SETUP --------------------
app = FastAPI()

# Create database tables
Base.metadata.create_all(bind=engine)

# -------------------- CORS --------------------
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://autopilotai.dev",
    "https://www.autopilotai.dev",
    "https://autopilotai-frontend.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------- ROUTES --------------------
app.include_router(auth_router, prefix="/api/auth")
app.include_router(history_router, prefix="/api")
app.include_router(stripe_router, prefix="/api/stripe")
app.include_router(profile_router, prefix="/api")
app.include_router(usage_router, prefix="/api/auth")
app.include_router(dashboard_router, prefix="/api")
app.include_router(work_router, prefix="/api")

# AI Routes
app.include_router(content_router, prefix="/api/content")
app.include_router(email_router, prefix="/api/email")
app.include_router(ads_router, prefix="/api/ads")

# -------------------- DEBUG: PRINT ROUTES --------------------
@app.on_event("startup")
def print_routes():
    print("===== REGISTERED ROUTES =====")
    for r in app.routes:
        print(r.path, r.methods)
    print("===== END ROUTES =====")

# -------------------- ROOT --------------------
@app.get("/")
def read_root():
    return {"message": "AutopilotAI backend running"}
