from dotenv import load_dotenv
load_dotenv()

import os
import sys

print("PRICE_GROWTH FROM ENV:", os.getenv("PRICE_GROWTH"))
print(">>> Python executable:", sys.executable)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# -------------------- DATABASE --------------------
from app.database.session import engine
from app.database import models   # ensures all models register
from app.database.models import Base

# -------------------- ROUTERS --------------------
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
from app.ai import image_routes
from app.ai.growth_pack_routes import router as growth_pack_router
from app.routes.restaurant_websites import router as restaurant_websites_router
from app.routes.restaurant_websites import domains_router  # ✅ NEW
from app.routes import websites_routes
from app.routes import dashboard_websites_routes

# -------------------- APP SETUP --------------------
app = FastAPI()

# -------------------- CREATE DATABASE TABLES --------------------
Base.metadata.create_all(bind=engine)

# -------------------- CORS (FIXED – NO CONFLICTS) --------------------
app.add_middleware(
    CORSMiddleware,
    # allow autopilotai.dev, www, vercel previews, localhost
    allow_origin_regex=r"^https://(www\.)?autopilotai\.dev$|^https://.*\.vercel\.app$|^http://localhost:3000$|^http://127\.0\.0\.1:3000$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=86400,
)

# -------------------- ROUTES --------------------
app.include_router(auth_router, prefix="/api/auth")
app.include_router(history_router, prefix="/api")
app.include_router(stripe_router, prefix="/api/stripe")
app.include_router(profile_router, prefix="/api")
app.include_router(usage_router, prefix="/api/auth")
app.include_router(dashboard_router, prefix="/api")
app.include_router(work_router, prefix="/api")
app.include_router(image_routes.router, prefix="/api")
app.include_router(growth_pack_router, prefix="/api")

# 🔥 dashboard website builder FIRST
app.include_router(dashboard_websites_routes.router)

# public website renderers AFTER
app.include_router(restaurant_websites_router)

# ✅ domains resolver (for custom domain routing)
app.include_router(domains_router)

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
