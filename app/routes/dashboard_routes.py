import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.utils.auth import get_current_user
from app.database.session import SessionLocal
from app.database.models import User, DashboardSettings, Task

router = APIRouter()


# -------------------------
# Helpers
# -------------------------
def _get_or_create_settings(db, user_id: int) -> DashboardSettings:
    s = db.query(DashboardSettings).filter(DashboardSettings.user_id == user_id).first()
    if not s:
        s = DashboardSettings(user_id=user_id)
        db.add(s)
        db.commit()
        db.refresh(s)
    return s


def _require_subscribed(user: User):
    # Gate AI Suggestions for subscribed users only
    # ✅ allowed: basic, growth, pro
    # ❌ blocked: free
    if (user.subscription_plan or "free").lower() == "free":
        raise HTTPException(403, "AI Suggestions are available for subscribed users only.")


# -------------------------
# Settings schemas
# -------------------------
class SettingsUpdate(BaseModel):
    stocks: list[str] | None = None
    cryptos: list[str] | None = None
    currency_pairs: list[str] | None = None
    city: str | None = None
    widgets_order: list[str] | None = None
    widgets_collapsed: dict | None = None


@router.get("/dashboard/settings")
def get_settings(user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        s = _get_or_create_settings(db, user.id)
        return {
            "stocks": json.loads(s.stocks_json or "[]"),
            "cryptos": json.loads(s.cryptos_json or "[]"),
            "currency_pairs": json.loads(s.currency_pairs_json or "[]"),
            "city": s.city or "",
            "widgets_order": json.loads(s.widgets_order_json or "[]"),
            "widgets_collapsed": json.loads(s.widgets_collapsed_json or "{}"),
        }
    finally:
        db.close()


@router.post("/dashboard/settings")
def update_settings(payload: SettingsUpdate, user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        s = _get_or_create_settings(db, user.id)

        if payload.stocks is not None:
            s.stocks_json = json.dumps(payload.stocks)
        if payload.cryptos is not None:
            s.cryptos_json = json.dumps(payload.cryptos)
        if payload.currency_pairs is not None:
            s.currency_pairs_json = json.dumps(payload.currency_pairs)
        if payload.city is not None:
            s.city = payload.city
        if payload.widgets_order is not None:
            s.widgets_order_json = json.dumps(payload.widgets_order)
        if payload.widgets_collapsed is not None:
            s.widgets_collapsed_json = json.dumps(payload.widgets_collapsed)

        db.commit()
        return {"message": "Dashboard settings updated"}
    finally:
        db.close()


# -------------------------
# Tasks
# -------------------------
class TaskCreate(BaseModel):
    text: str


@router.get("/dashboard/tasks")
def list_tasks(user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        tasks = (
            db.query(Task)
            .filter(Task.user_id == user.id)
            .order_by(Task.created_at.desc())
            .all()
        )
        return [
            {"id": t.id, "text": t.text, "is_done": t.is_done, "created_at": t.created_at.isoformat()}
            for t in tasks
        ]
    finally:
        db.close()


@router.post("/dashboard/tasks")
def create_task(payload: TaskCreate, user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        t = Task(user_id=user.id, text=payload.text.strip(), is_done=False)
        db.add(t)
        db.commit()
        db.refresh(t)
        return {"id": t.id, "text": t.text, "is_done": t.is_done}
    finally:
        db.close()


@router.post("/dashboard/tasks/{task_id}/toggle")
def toggle_task(task_id: int, user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        t = db.query(Task).filter(Task.id == task_id, Task.user_id == user.id).first()
        if not t:
            raise HTTPException(404, "Task not found")
        t.is_done = not t.is_done
        db.commit()
        return {"message": "Task updated", "is_done": t.is_done}
    finally:
        db.close()


@router.delete("/dashboard/tasks/{task_id}")
def delete_task(task_id: int, user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        t = db.query(Task).filter(Task.id == task_id, Task.user_id == user.id).first()
        if not t:
            raise HTTPException(404, "Task not found")
        db.delete(t)
        db.commit()
        return {"message": "Task deleted"}
    finally:
        db.close()


# -------------------------
# AI Suggestions (gated)
# Step 1: return placeholder so frontend wiring + gating works.
# Step 2 later: connect OpenAI + profile_context for real suggestions.
# -------------------------
@router.get("/dashboard/ai-suggestions")
def ai_suggestions(user: User = Depends(get_current_user)):
    _require_subscribed(user)

    return {
        "content_idea": "Try a short post: “3 ways to automate your marketing this week.”",
        "email_idea": "Follow-up email: keep it to 4 lines, ask one clear question, include CTA.",
        "ad_angle": "Focus on time-saved: “Replace your marketing team with 1 dashboard.”",
        "business_tip": "Consistency beats intensity — schedule 1 daily action and stick to it."
    }


# ==============================
# DASHBOARD: MARKETS
# ==============================
@router.get("/dashboard/markets")
def get_markets(user: User = Depends(get_current_user)):
    stocks = ["AAPL", "TSLA", "MSFT"]

    data = [
        {"symbol": "AAPL", "price": 192.3, "change": 0.8},
        {"symbol": "TSLA", "price": 238.4, "change": 1.9},
        {"symbol": "MSFT", "price": 421.7, "change": 0.6},
    ]

    return {
        "primary": data[0],
        "all": data,
    }


# ==============================
# DASHBOARD: CRYPTO
# ==============================
@router.get("/dashboard/crypto")
def get_crypto(user: User = Depends(get_current_user)):
    data = [
        {"symbol": "BTC", "price": 67420, "change": 2.1},
        {"symbol": "ETH", "price": 3580, "change": 1.4},
        {"symbol": "SOL", "price": 148, "change": 3.2},
    ]

    return {
        "primary": data[0],
        "all": data,
    }


# ==============================
# DASHBOARD: WEATHER
# ==============================
@router.get("/dashboard/weather")
def get_weather(user: User = Depends(get_current_user)):
    return {
        "temp": 29,
        "condition": "Sunny",
        "location": "Chiang Mai",
    }


# ==============================
# DASHBOARD: AI INSIGHT (SUBSCRIBERS ONLY)
# ==============================
@router.get("/dashboard/ai-insight")
def get_ai_insight(user: User = Depends(get_current_user)):
    if user.subscription_plan == "free":
        return {
            "locked": True
        }

    return {
        "locked": False,
        "text": "Short-form posts with a strong hook are outperforming long content this week."
    }
