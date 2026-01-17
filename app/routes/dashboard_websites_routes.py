from fastapi import APIRouter, HTTPException, Depends, Body
from sqlalchemy.orm import Session
import json
import re
import os
from typing import Optional, Any, Dict, List

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

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _clean_text(v: Any) -> str:
    if v is None:
        return ""
    return str(v).strip()


def _safe_json_loads(s: str) -> Optional[dict]:
    try:
        return json.loads(s)
    except Exception:
        return None


def _is_nonempty_str(v: Any) -> bool:
    return isinstance(v, str) and v.strip() != ""


def _ensure_list(v: Any) -> List[Any]:
    return v if isinstance(v, list) else []


def _ensure_dict(v: Any) -> Dict[str, Any]:
    return v if isinstance(v, dict) else {}


def _merge_defaults(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Shallow merge, but preserves nested dict keys if override provides partial dicts.
    """
    out = dict(base or {})
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = {**out[k], **v}
        else:
            out[k] = v
    return out


def _normalize_full_content(content: Dict[str, Any], defaults: Dict[str, Any]) -> Dict[str, Any]:
    """
    Forces all expected sections to exist and be non-placeholder-ish.
    If AI returns partial JSON, we patch missing parts from defaults.
    """
    content = _ensure_dict(content)

    # Always ensure top-level keys exist
    for key in [
        "hero", "highlight", "about", "services", "trust",
        "process", "testimonial", "faq", "cta", "gallery", "contact"
    ]:
        if key not in content or content[key] is None:
            content[key] = defaults.get(key)

    # HERO
    hero = _ensure_dict(content.get("hero"))
    hero_defaults = _ensure_dict(defaults.get("hero"))
    hero = _merge_defaults(hero_defaults, hero)

    # Force non-empty headline/subheadline/cta_text
    if not _is_nonempty_str(hero.get("headline")):
        hero["headline"] = hero_defaults.get("headline", "")
    if not _is_nonempty_str(hero.get("subheadline")):
        hero["subheadline"] = hero_defaults.get("subheadline", "")
    if not _is_nonempty_str(hero.get("cta_text")):
        hero["cta_text"] = hero_defaults.get("cta_text", "Contact us")
    if "image" not in hero:
        hero["image"] = None
    content["hero"] = hero

    # HIGHLIGHT
    highlight = _ensure_dict(content.get("highlight"))
    highlight_defaults = _ensure_dict(defaults.get("highlight"))
    highlight = _merge_defaults(highlight_defaults, highlight)
    if not _is_nonempty_str(highlight.get("headline")):
        highlight["headline"] = highlight_defaults.get("headline", "")
    if not _is_nonempty_str(highlight.get("subheadline")):
        highlight["subheadline"] = highlight_defaults.get("subheadline", "")
    content["highlight"] = highlight

    # ABOUT
    about = _ensure_dict(content.get("about"))
    about_defaults = _ensure_dict(defaults.get("about"))
    about = _merge_defaults(about_defaults, about)
    paragraphs = _ensure_list(about.get("paragraphs"))
    if len([p for p in paragraphs if _is_nonempty_str(p)]) < 2:
        about["paragraphs"] = about_defaults.get("paragraphs", ["", ""])
    if "image" not in about:
        about["image"] = None
    content["about"] = about

    # SERVICES
    services = _ensure_dict(content.get("services"))
    services_defaults = _ensure_dict(defaults.get("services"))
    services = _merge_defaults(services_defaults, services)
    if not _is_nonempty_str(services.get("title")):
        services["title"] = services_defaults.get("title", "Services")
    items = _ensure_list(services.get("items"))
    # Ensure 3 items minimum
    if len(items) < 3:
        services["items"] = services_defaults.get("items", [])
    else:
        # ensure each item has title/description/image
        normalized_items = []
        for it in items[:5]:
            it = _ensure_dict(it)
            if not _is_nonempty_str(it.get("title")):
                it["title"] = "Service"
            if not _is_nonempty_str(it.get("description")):
                it["description"] = "Clear, reliable service tailored to your needs."
            if "image" not in it:
                it["image"] = None
            normalized_items.append(it)
        services["items"] = normalized_items
    content["services"] = services

    # TRUST
    trust = _ensure_dict(content.get("trust"))
    trust_defaults = _ensure_dict(defaults.get("trust"))
    trust = _merge_defaults(trust_defaults, trust)
    trust_items = _ensure_list(trust.get("items"))
    if len([t for t in trust_items if _is_nonempty_str(t)]) < 3:
        trust["items"] = trust_defaults.get("items", [])
    content["trust"] = trust

    # PROCESS
    process = _ensure_dict(content.get("process"))
    process_defaults = _ensure_dict(defaults.get("process"))
    process = _merge_defaults(process_defaults, process)
    steps = _ensure_list(process.get("steps"))
    if len(steps) < 3:
        process["steps"] = process_defaults.get("steps", [])
    else:
        norm_steps = []
        for st in steps[:5]:
            st = _ensure_dict(st)
            if not _is_nonempty_str(st.get("title")):
                st["title"] = "Step"
            if not _is_nonempty_str(st.get("description")):
                st["description"] = "Short, clear explanation of what happens in this step."
            norm_steps.append(st)
        process["steps"] = norm_steps
    content["process"] = process

    # TESTIMONIAL
    testimonial = _ensure_dict(content.get("testimonial"))
    testimonial_defaults = _ensure_dict(defaults.get("testimonial"))
    testimonial = _merge_defaults(testimonial_defaults, testimonial)
    if not _is_nonempty_str(testimonial.get("quote")):
        testimonial["quote"] = testimonial_defaults.get("quote", "")
    if not _is_nonempty_str(testimonial.get("author")):
        testimonial["author"] = testimonial_defaults.get("author", "Customer")
    content["testimonial"] = testimonial

    # FAQ
    faq = _ensure_dict(content.get("faq"))
    faq_defaults = _ensure_dict(defaults.get("faq"))
    faq = _merge_defaults(faq_defaults, faq)
    faq_items = _ensure_list(faq.get("items"))
    if len(faq_items) < 3:
        faq["items"] = faq_defaults.get("items", [])
    else:
        norm_faq = []
        for qa in faq_items[:6]:
            qa = _ensure_dict(qa)
            if not _is_nonempty_str(qa.get("q")):
                qa["q"] = "Question?"
            if not _is_nonempty_str(qa.get("a")):
                qa["a"] = "Clear, helpful answer."
            norm_faq.append(qa)
        faq["items"] = norm_faq
    content["faq"] = faq

    # CTA
    cta = _ensure_dict(content.get("cta"))
    cta_defaults = _ensure_dict(defaults.get("cta"))
    cta = _merge_defaults(cta_defaults, cta)
    if not _is_nonempty_str(cta.get("headline")):
        cta["headline"] = cta_defaults.get("headline", "")
    if not _is_nonempty_str(cta.get("subheadline")):
        cta["subheadline"] = cta_defaults.get("subheadline", "")
    if not _is_nonempty_str(cta.get("button")):
        cta["button"] = cta_defaults.get("button", "Contact us")
    content["cta"] = cta

    # GALLERY
    gallery = _ensure_dict(content.get("gallery"))
    gallery_defaults = _ensure_dict(defaults.get("gallery"))
    gallery = _merge_defaults(gallery_defaults, gallery)
    if "images" not in gallery or not isinstance(gallery.get("images"), list):
        gallery["images"] = []
    content["gallery"] = gallery

    # CONTACT (user fills, but structure must exist)
    contact = _ensure_dict(content.get("contact"))
    contact_defaults = _ensure_dict(defaults.get("contact"))
    contact = _merge_defaults(contact_defaults, contact)
    for k in ["phone", "email", "address", "city"]:
        if k not in contact:
            contact[k] = contact_defaults.get(k, "")
    content["contact"] = contact

    return content


# =========================
# AI-LITE INFERENCE
# =========================

def infer_ai_input_from_prompt(prompt: str) -> dict:
    p = (prompt or "").lower()

    business_type = "business"
    if any(w in p for w in ["restaurant", "pizza", "burger", "cafe", "coffee", "food"]):
        business_type = "restaurant"

    city = ""
    city_match = re.search(r"in ([a-zA-Z\s]{2,30})", prompt or "")
    if city_match:
        city = city_match.group(1).strip().title()

    goal = "Contact us"
    if any(w in p for w in ["book", "booking", "appointment"]):
        goal = "Book an appointment"
    elif any(w in p for w in ["contact", "call", "lead"]):
        goal = "Contact us"
    elif any(w in p for w in ["buy", "order", "sell", "quote", "pricing"]):
        goal = "Get a free quote"
    elif business_type == "restaurant":
        goal = "Reserve a table"

    return {
        "business_type": business_type,
        "city": city,
        "primary_goal": goal,
        "raw_prompt": prompt,
    }


# =========================
# DEFAULTS (FULL BUILDER COVERAGE)
# =========================

def build_default_content(template: str, ai_input: dict, username: str) -> dict:
    name = username.replace("-", " ").title()
    city = _clean_text(ai_input.get("city"))
    goal = _clean_text(ai_input.get("primary_goal")) or "Contact us"

    city_line = f" in {city}" if city else ""

    if template == "restaurant":
        hero_headline = f"{name}{city_line}"
        hero_sub = "Fresh food, warm atmosphere, and a menu your customers will remember."
        cta_text = "View menu" if goal.lower().startswith("reserve") is False else goal
        services_title = "Popular choices"
        services_items = [
            {"title": "Signature dishes", "description": "A menu built around flavor, freshness, and consistency.", "image": None},
            {"title": "Dine-in experience", "description": "Comfortable seating, friendly service, and a relaxed vibe.", "image": None},
            {"title": "Takeaway & delivery", "description": "Fast, reliable pickup or delivery when you need it.", "image": None},
        ]
        trust_items = [
            "Fresh ingredients and consistent quality",
            "Friendly staff and quick service",
            "Clear pricing and a welcoming atmosphere",
        ]
        process_steps = [
            {"title": "Choose your favorites", "description": "Browse the menu and pick what you love."},
            {"title": "Order or reserve", "description": "Reserve a table or place an order in seconds."},
            {"title": "Enjoy", "description": "Great food, great service — every time."},
        ]
        faq_items = [
            {"q": "Do you take reservations?", "a": "Yes — you can reserve a table through our contact section."},
            {"q": "Do you offer takeaway or delivery?", "a": "Yes — availability depends on your location and time."},
            {"q": "Do you have vegetarian options?", "a": "Yes — we offer vegetarian-friendly choices."},
        ]
        testimonial = {"quote": "Great food, friendly service, and everything felt easy from start to finish.", "author": "Local customer"}
        cta = {
            "headline": "Want to reserve a table?",
            "subheadline": "Reach out and we’ll confirm quickly.",
            "button": "Reserve a table",
        }
    else:
        hero_headline = f"{name}{city_line}"
        hero_sub = "Clear communication, honest service, and results you can trust."
        cta_text = goal
        services_title = "What we do"
        services_items = [
            {"title": "Professional service", "description": "Reliable, high-quality work tailored to your needs.", "image": None},
            {"title": "Clear communication", "description": "You always know what’s happening and what to expect.", "image": None},
            {"title": "Results that matter", "description": "Focused on outcomes, not unnecessary complexity.", "image": None},
        ]
        trust_items = [
            "Fast response and clear next steps",
            "Transparent pricing and no surprises",
            "High-quality work and attention to detail",
        ]
        process_steps = [
            {"title": "Tell us what you need", "description": "A quick message is enough to get started."},
            {"title": "Get a clear plan", "description": "We outline the next steps and confirm details."},
            {"title": "We deliver", "description": "High-quality results with clear communication."},
        ]
        faq_items = [
            {"q": "How fast do you respond?", "a": "Typically the same day — often within a few hours."},
            {"q": "Do you offer fixed pricing?", "a": "Yes — for many requests we can provide a clear quote up front."},
            {"q": "How do I get started?", "a": "Send a message using the contact section and we’ll guide you."},
        ]
        testimonial = {"quote": "Everything was smooth, professional, and easy from start to finish.", "author": "Customer"}
        cta = {
            "headline": "Ready to take the next step?",
            "subheadline": "Send a message and we’ll get back to you quickly.",
            "button": goal,
        }

    defaults = {
        "hero": {
            "headline": hero_headline,
            "subheadline": hero_sub,
            "cta_text": cta_text,
            "image": None,
        },
        "highlight": {
            "headline": "Make a strong first impression.",
            "subheadline": "Warm, trustworthy design — plus copy your customers actually understand.",
        },
        "about": {
            "paragraphs": [
                "We keep things simple: clear communication, consistent quality, and a great customer experience.",
                "If you want a website that looks premium and drives action, you’re in the right place.",
            ],
            "image": None,
        },
        "services": {
            "title": services_title,
            "items": services_items,
        },
        "trust": {
            "items": trust_items,
        },
        "process": {
            "steps": process_steps,
        },
        "testimonial": testimonial,
        "faq": {
            "items": faq_items,
        },
        "cta": cta,
        "gallery": {
            "images": [],
        },
        "contact": {
            "phone": "",
            "email": "",
            "address": "",
            "city": city,
        },
    }
    return defaults


# =========================
# OPENAI GENERATION (FULL BUILDER COVERAGE)
# =========================

def ai_generate_content_with_openai(
    template: str,
    ai_input: dict,
    username: str,
) -> Optional[dict]:
    """
    Must return FULL schema coverage for builder sections:
    hero, highlight, about, services, trust, process, testimonial, faq, cta, gallery, contact
    """
    if not _openai_client:
        return None

    prompt_text = _clean_text(ai_input.get("raw_prompt"))
    if len(prompt_text) < 10:
        return None

    city = _clean_text(ai_input.get("city"))
    business_name = username.replace("-", " ").title()
    goal = _clean_text(ai_input.get("primary_goal")) or "Contact us"

    SYSTEM = """
You are a senior website copywriter.

Rules:
- Output STRICT JSON only (no markdown, no commentary).
- DO NOT use placeholders like "Your Business Name", "Short description".
- Be specific to the business description.
- Write like this website is ready to publish.
- Tone should feel warm, modern, trustworthy.
- No fake stats or awards.
"""

    USER = f"""
Business name: {business_name}
Business type: {template}
City (if relevant): {city}
Primary goal CTA: {goal}

User description:
{prompt_text}

Return STRICT JSON with ALL fields present and filled:

{{
  "hero": {{
    "headline": "Outcome + who + city (if relevant)",
    "subheadline": "1–2 sentences, specific",
    "cta_text": "{goal}",
    "image": null
  }},
  "highlight": {{
    "headline": "short strong line",
    "subheadline": "supporting line"
  }},
  "about": {{
    "paragraphs": ["2–3 short paragraphs"],
    "image": null
  }},
  "services": {{
    "title": "Services",
    "items": [
      {{ "title": "Service 1", "description": "1 sentence, outcome-based", "image": null }},
      {{ "title": "Service 2", "description": "1 sentence, outcome-based", "image": null }},
      {{ "title": "Service 3", "description": "1 sentence, outcome-based", "image": null }}
    ]
  }},
  "trust": {{
    "items": ["reason 1", "reason 2", "reason 3"]
  }},
  "process": {{
    "steps": [
      {{ "title": "Step 1", "description": "short" }},
      {{ "title": "Step 2", "description": "short" }},
      {{ "title": "Step 3", "description": "short" }}
    ]
  }},
  "testimonial": {{
    "quote": "Realistic short testimonial (no stats)",
    "author": "Name or 'Customer'"
  }},
  "faq": {{
    "items": [
      {{ "q": "Question 1?", "a": "Answer 1." }},
      {{ "q": "Question 2?", "a": "Answer 2." }},
      {{ "q": "Question 3?", "a": "Answer 3." }}
    ]
  }},
  "cta": {{
    "headline": "CTA headline",
    "subheadline": "CTA supporting line",
    "button": "{goal}"
  }},
  "gallery": {{
    "images": []
  }},
  "contact": {{
    "phone": "",
    "email": "",
    "address": "",
    "city": "{city}"
  }}
}}

Important:
- Make service titles match the business.
- Make FAQ relevant to the business.
- Trust items should be believable.
"""

    try:
        resp = _openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": USER},
            ],
            temperature=0.65,
            max_tokens=1400,
        )

        raw = (resp.choices[0].message.content or "").strip()
        data = _safe_json_loads(raw)
        if not isinstance(data, dict):
            return None
        return data
    except Exception:
        return None


# =========================
# CREATE WEBSITE (CANONICAL)
# =========================

@router.post("/create")
def create_website(
    payload: dict = Body(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Pricing rules:
    - free: 1 site, draft only, 1 page
    - starter: 1 site, published, 1 page
    - pro: 1 site, published, up to 3 pages
    """

    plan = (user.subscription_plan or "free").lower()

    # 1 website per user (hard limit)
    if db.query(Website).filter(Website.user_id == user.id).count() >= 1:
        raise HTTPException(status_code=403, detail="Only one website allowed")

    username = (payload.get("username") or "").strip().lower()
    prompt = (payload.get("prompt") or "").strip()

    if not username:
        raise HTTPException(status_code=400, detail="Missing username")

    if db.query(Website).filter(Website.username == username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    ai_input = infer_ai_input_from_prompt(prompt)
    template = ai_input["business_type"]

    # -------------------------
    # PLAN → PAGE LIMITS
    # -------------------------
    max_pages = 3 if plan == "pro" else 1

    structure = generate_ai_structure(
        business_type=template,
        goal=_clean_text(ai_input.get("primary_goal")) or "conversions",
        version=1,
    )

    # Inject plan metadata (NO DB schema changes)
    structure["plan"] = {
        "name": plan,
        "max_pages": max_pages,
        "can_publish": plan in ("starter", "pro"),
    }

    # Build strong defaults first (full schema)
    defaults = build_default_content(template, ai_input, username)

    # Try OpenAI, then normalize/patch to guarantee full coverage
    ai_content = ai_generate_content_with_openai(template, ai_input, username) or {}
    content = _normalize_full_content(ai_content, defaults)

    # Publishing status is tied to subscription plan
    publish_status = "published" if plan in ("starter", "pro") else "draft"

    site = Website(
        user_id=user.id,
        username=username,
        template=template,
        content_json=json.dumps(content),
        ai_structure_json=json.dumps(structure),
        publish_status=publish_status,
    )

    db.add(site)
    db.commit()

    return {
        "ok": True,
        "username": username,
        "redirect": f"/r/{username}?edit=1",
        "plan": plan,
        "max_pages": max_pages,
        "published": plan in ("starter", "pro"),
    }
