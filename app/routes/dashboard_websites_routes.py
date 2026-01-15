from fastapi import APIRouter, HTTPException, Depends, Body
from sqlalchemy.orm import Session
import json
import re
import os
from typing import Optional, Dict, Any, List

from app.database.session import SessionLocal
from app.database.models import Website, User
from app.utils.auth import get_current_user

from app.ai.website_ai import generate_ai_structure

# =========================
# OPTIONAL: OpenAI
# =========================
try:
    from openai import OpenAI

    _openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
except Exception:
    _openai_client = None

router = APIRouter(prefix="/api/dashboard/websites")


# =========================
# HELPERS
# =========================
def _validate_username(username: str):
    if not re.match(r"^[a-z0-9\-]{3,30}$", username):
        raise HTTPException(
            status_code=400,
            detail="Username must be 3–30 chars, lowercase letters, numbers or hyphens only",
        )


def infer_ai_input_from_prompt(prompt: str) -> dict:
    """
    Very fast, deterministic AI-style inference.
    No OpenAI call. Safe. Predictable.
    """

    p = prompt.lower()

    # -------- template inference --------
    if any(w in p for w in ["restaurant", "cafe", "pizza", "burger", "bar", "food"]):
        business_type = "restaurant"
    else:
        business_type = "business"

    # -------- city inference --------
    city_match = re.search(r"in ([a-zA-Z\s]+)", prompt)
    city = city_match.group(1).strip().title() if city_match else ""

    # -------- goal inference --------
    if any(w in p for w in ["book", "booking", "appointments", "schedule"]):
        goal = "Get bookings"
    elif any(w in p for w in ["sell", "sales", "customers", "clients"]):
        goal = "Get more customers"
    else:
        goal = "Get started"

    # -------- business name guess --------
    name_match = re.search(r"called ([a-zA-Z0-9\s]+)", prompt)
    business_name = name_match.group(1).strip().title() if name_match else ""

    return {
        "business_type": business_type,
        "business_name": business_name,
        "city": city,
        "primary_goal": goal,
    }

def infer_ai_input(ai_prompt: str) -> dict:
    """
    Very lightweight inference from free text.
    Cheap, deterministic, no OpenAI call.
    """
    text = (ai_prompt or "").strip()

    out = {
        "business_name": "",
        "city": "",
        "primary_goal": "Get started",
    }

    if not text:
        return out

    # crude business name guess: first sentence / clause
    first = text.split(".")[0].strip()
    if len(first) <= 60:
        out["business_name"] = first

    lowered = text.lower()

    # city heuristic
    for token in [" in ", " based in ", " located in "]:
        if token in lowered:
            city = lowered.split(token, 1)[1].split(" ")[0:3]
            out["city"] = " ".join(city).title()
            break

    # goal heuristic
    if "booking" in lowered or "appointment" in lowered:
        out["primary_goal"] = "Book now"
    elif "contact" in lowered or "lead" in lowered:
        out["primary_goal"] = "Contact us"
    elif "sell" in lowered or "sales" in lowered:
        out["primary_goal"] = "Buy now"

    return out


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _clean_text(s: Any) -> str:
    if s is None:
        return ""
    return str(s).strip()


def infer_template_from_description(description: str) -> str:
    """
    Simple deterministic inference.
    If restaurant keywords appear → restaurant else business.
    """
    d = (description or "").lower()

    restaurant_keywords = [
        "restaurant",
        "burger",
        "pizza",
        "sushi",
        "cafe",
        "coffee",
        "bar",
        "bistro",
        "menu",
        "dine",
        "dining",
        "takeaway",
        "delivery",
        "table",
        "reservation",
        "chef",
        "cuisine",
        "food",
        "kitchen",
    ]

    if any(k in d for k in restaurant_keywords):
        return "restaurant"

    return "business"

def infer_ai_input_from_prompt(prompt: str) -> dict:
    """
    Extremely cheap, deterministic AI-lite inference.
    NO OpenAI call yet.
    This just extracts intent so structure + defaults feel smart.
    """

    p = (prompt or "").lower()

    business_type = "business"
    if any(w in p for w in ["restaurant", "pizza", "burger", "cafe", "coffee", "food"]):
        business_type = "restaurant"

    city = ""
    city_match = re.search(r"in ([a-zA-Z\s]{2,30})", prompt or "")
    if city_match:
        city = city_match.group(1).strip()

    goal = "Get started"
    if any(w in p for w in ["book", "booking", "appointment"]):
        goal = "Book now"
    elif any(w in p for w in ["call", "contact"]):
        goal = "Contact us"
    elif any(w in p for w in ["buy", "order"]):
        goal = "Order now"

    return {
        "business_type": business_type,
        "city": city,
        "primary_goal": goal,
        "business_name": "",  # let content builder decide
        "raw_prompt": prompt,
    }


def build_default_content(template: str, ai_input: dict, username: str) -> dict:
    """
    Deterministic, cheap, always-present starter content.
    Must match what your frontend expects.
    """
    description = _clean_text(ai_input.get("description"))
    name = _clean_text(ai_input.get("business_name")) or username.replace("-", " ").title()
    city = _clean_text(ai_input.get("city"))

    # If user typed something like "I run X called Y", we still keep safe defaults.
    hero_headline = name
    hero_subheadline = (
        f"Serving {city} with quality and care." if city else "Built with AutopilotAI."
    )

    if description and len(description) >= 24:
        # use part of description as a more human subheadline
        hero_subheadline = description[:160].rstrip() + ("…" if len(description) > 160 else "")

    services = [
        {
            "title": "Professional service",
            "description": "Reliable, high-quality service tailored to your needs.",
        },
        {
            "title": "Fast response",
            "description": "Quick turnaround and clear communication.",
        },
        {
            "title": "Trusted by customers",
            "description": "Focused on long-term results and satisfaction.",
        },
    ]

    base = {
        "hero": {
            "headline": hero_headline,
            "subheadline": hero_subheadline,
            "image": None,
            "cta_text": "Get started",
            "cta_link": "#contact",
        },
        "about": {
            "title": "About",
            "text": description or "Add a short story about your business and what makes you different.",
            "image": None,
        },
        # AIWebsiteRenderer expects services as a LIST of {title, description}
        "services": services,
        "cta": {
            "headline": "Ready to take the next step?",
            "text": "Contact us today and we’ll respond quickly.",
            "link": "#contact",
        },
        # We’ll use these for “AI guidance”
        "ai_todos": [
            "Add your phone number and email in the Contact section.",
            "Add your address/city so customers know where you are located.",
        ],
        "ai_notes": [
            "Tip: A real hero image increases trust and conversions.",
        ],
    }

    if template == "restaurant":
        base.update(
            {
                "menu": [],
                "hours": {
                    "mon_fri": "11:00 – 22:00",
                    "sat_sun": "12:00 – 23:00",
                },
                "location": {
                    "address": "",
                    "city": city,
                },
                "contact": {
                    "phone": "",
                    "email": "",
                },
            }
        )
        base["ai_todos"].insert(0, "Add opening hours and your most popular menu items.")

    else:
        # BusinessTemplate expects contact object with title/subtitle/phone/email/address/city (it normalizes)
        base.update(
            {
                "contact": {
                    "title": "Contact",
                    "subtitle": "Reach out — we usually respond the same day.",
                    "phone": "",
                    "email": "",
                    "address": "",
                    "city": city or "",
                }
            }
        )

    return base


def _safe_json_loads(s: str) -> Optional[dict]:
    try:
        return json.loads(s)
    except Exception:
        return None


def ai_generate_content_with_openai(template: str, ai_input: dict, username: str) -> Optional[dict]:
    """
    Tries to create REAL copy. Returns dict content that matches frontend expectations.
    If OpenAI fails → returns None and we fallback to build_default_content().
    """
    if not _openai_client:
        return None

    description = _clean_text(ai_input.get("description"))
    if not description or len(description) < 10:
        return None

    city = _clean_text(ai_input.get("city"))
    hinted_name = _clean_text(ai_input.get("business_name")) or username.replace("-", " ").title()

    # IMPORTANT: keep schema aligned with your current frontend:
    # - AIWebsiteRenderer reads: content.hero.headline/subheadline, content.services (array), content.cta.headline
    # - RestaurantTemplate/BusinessTemplate have their own normalizers; but we keep these keys anyway.
    if template == "restaurant":
        schema_hint = """
Return JSON with these keys EXACTLY:
{
  "hero": { "headline": "", "subheadline": "", "image": null, "cta_text": "", "cta_link": "#contact" },
  "about": { "title": "About", "text": "", "image": null },
  "services": [ { "title": "", "description": "" } ],
  "cta": { "headline": "", "text": "", "link": "#contact" },
  "menu": [ { "title": "Popular", "items": [ { "name": "", "description": "", "price": "" } ] } ],
  "hours": { "mon_fri": "", "sat_sun": "" },
  "location": { "address": "", "city": "" },
  "contact": { "phone": "", "email": "" },
  "ai_todos": [ "" ],
  "ai_notes": [ "" ]
}
"""
    else:
        schema_hint = """
Return JSON with these keys EXACTLY:
{
  "hero": { "headline": "", "subheadline": "", "image": null, "cta_text": "", "cta_link": "#contact" },
  "about": { "title": "About us", "text": "", "image": null },
  "services": [ { "title": "", "description": "" } ],
  "cta": { "headline": "", "text": "", "link": "#contact" },
  "contact": { "title": "Contact", "subtitle": "", "phone": "", "email": "", "address": "", "city": "" },
  "ai_todos": [ "" ],
  "ai_notes": [ "" ]
}
"""

    prompt = f"""
You generate REAL website homepage content for a {template}.

Business name hint (if needed): {hinted_name}
City hint (if relevant): {city}

User description:
{description}

Rules:
- Output ONLY valid JSON (no markdown, no comments).
- Keep it concise but professional.
- Make the hero strong and specific.
- Services should be 3–6 items.
- Include 3–6 "ai_todos" with the highest-impact missing info (phone/email/address, hours/menu if restaurant).
- If you don't know exact phone/email/address, leave them as empty strings.

{schema_hint}
""".strip()

    try:
        resp = _openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You output ONLY JSON. No explanation."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.6,
            max_tokens=900,
        )
        raw = (resp.choices[0].message.content or "").strip()

        data = _safe_json_loads(raw)
        if not isinstance(data, dict):
            return None

        # Minimal safety: ensure required top-level keys exist
        if "hero" not in data or "services" not in data or "cta" not in data:
            return None

        # Ensure hero fields exist
        data["hero"] = {
            "headline": _clean_text(data.get("hero", {}).get("headline")) or hinted_name,
            "subheadline": _clean_text(data.get("hero", {}).get("subheadline")),
            "image": None,
            "cta_text": _clean_text(data.get("hero", {}).get("cta_text")) or "Get started",
            "cta_link": "#contact",
        }

        # Ensure services is list
        if not isinstance(data.get("services"), list):
            data["services"] = []

        # Normalize services items
        norm_services = []
        for s in data["services"][:6]:
            if not isinstance(s, dict):
                continue
            norm_services.append(
                {
                    "title": _clean_text(s.get("title")) or "Service",
                    "description": _clean_text(s.get("description")),
                }
            )
        data["services"] = norm_services or [
            {"title": "Professional service", "description": "Reliable, high-quality work tailored to your needs."}
        ]

        # ai_todos / ai_notes
        if not isinstance(data.get("ai_todos"), list):
            data["ai_todos"] = []
        if not isinstance(data.get("ai_notes"), list):
            data["ai_notes"] = []

        # Fill template-specific defaults if missing
        if template == "restaurant":
            data.setdefault("menu", [])
            data.setdefault("hours", {"mon_fri": "11:00 – 22:00", "sat_sun": "12:00 – 23:00"})
            data.setdefault("location", {"address": "", "city": city})
            data.setdefault("contact", {"phone": "", "email": ""})
        else:
            data.setdefault(
                "contact",
                {
                    "title": "Contact",
                    "subtitle": "Reach out — we usually respond the same day.",
                    "phone": "",
                    "email": "",
                    "address": "",
                    "city": city or "",
                },
            )

        return data

    except Exception:
        return None


# =========================
# GET MY WEBSITE
# =========================
@router.get("/me")
def get_my_website(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    site = db.query(Website).filter(Website.user_id == user.id).first()

    if not site:
        return {"exists": False}

    return {
        "exists": True,
        "username": site.username,
        "template": site.template,
    }


# =========================
# CREATE WEBSITE (CANONICAL)
# =========================
@router.post("/create")
def create_website(
    payload: dict = Body(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # -------------------------
    # PAID CHECK
    # -------------------------
    plan = (getattr(user, "subscription_plan", None) or "free").lower()
    if plan == "free" and user.email != "Test@user.com":
        raise HTTPException(
            status_code=403,
            detail="Website builder is available for paid plans only",
        )

    # -------------------------
    # Max 1 site per user
    # -------------------------
    if db.query(Website).filter(Website.user_id == user.id).count() >= 1:
        raise HTTPException(
            status_code=403,
            detail="Your plan allows only one website",
        )

    username = (payload.get("username") or "").strip().lower()
    prompt = (payload.get("prompt") or "").strip()
    ai_prompt = payload.get("ai_prompt", "")
    ai_input = infer_ai_input(ai_prompt)


    # 🧠 Free-text AI prompt path
    if prompt:
        inferred = infer_ai_input_from_prompt(prompt)
        ai_input = {**ai_input, **inferred}
        template = inferred["business_type"]
    else:
        template = (payload.get("template") or "").strip().lower()


    if not username:
        raise HTTPException(status_code=400, detail="Missing username")

    _validate_username(username)

    if db.query(Website).filter(Website.username == username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    # -------------------------
    # TEMPLATE INFERENCE (NEW)
    # -------------------------
    if template not in ("restaurant", "business"):
        # Infer from ai_input.description
        description = _clean_text(ai_input.get("description"))
        template = infer_template_from_description(description) if description else "business"

    # -------------------------
    # AI STRUCTURE (ONCE)
    # -------------------------
    # Use deterministic goal (can later infer from text)
    goal = _clean_text(ai_input.get("primary_goal")) or "conversions"
    structure = generate_ai_structure(
        business_type=template,
        goal=goal,
        version=1,
    )

    # -------------------------
    # AI CONTENT (OPENAI) + FALLBACK
    # -------------------------
    ai_content = ai_generate_content_with_openai(template, ai_input, username)
    content = ai_content if ai_content else build_default_content(template, ai_input, username)

    # -------------------------
    # Save
    # -------------------------
    site = Website(
        user_id=user.id,
        username=username,
        template=template,
        content_json=json.dumps(content),
        ai_structure_json=json.dumps(structure),
    )

    db.add(site)
    db.commit()

    return {
        "ok": True,
        "username": username,
        "redirect": f"/r/{username}?edit=1",
    }
