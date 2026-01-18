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
    Merge AI content with defaults WITHOUT overwriting real AI copy.
    Defaults are used ONLY when AI content is missing or empty.
    """
    content = _ensure_dict(content)
    defaults = _ensure_dict(defaults)

    # Helper: non-empty string
    def has_text(v):
        return isinstance(v, str) and v.strip() != ""

    # -------------------------
    # HERO
    # -------------------------
    hero = _ensure_dict(content.get("hero"))
    hero_defaults = _ensure_dict(defaults.get("hero"))

    if not has_text(hero.get("headline")):
        hero["headline"] = hero_defaults.get("headline", "")
    if not has_text(hero.get("subheadline")):
        hero["subheadline"] = hero_defaults.get("subheadline", "")
    if not has_text(hero.get("cta_text")):
        hero["cta_text"] = hero_defaults.get("cta_text", "Get started")
    hero["image"] = hero.get("image", None)

    content["hero"] = hero

    # -------------------------
    # HIGHLIGHT
    # -------------------------
    highlight = _ensure_dict(content.get("highlight"))
    highlight_defaults = _ensure_dict(defaults.get("highlight"))

    if not has_text(highlight.get("headline")):
        highlight["headline"] = highlight_defaults.get("headline", "")
    if not has_text(highlight.get("subheadline")):
        highlight["subheadline"] = highlight_defaults.get("subheadline", "")

    content["highlight"] = highlight

    # -------------------------
    # ABOUT  ✅ CRITICAL FIX
    # -------------------------
    about = _ensure_dict(content.get("about"))
    about_defaults = _ensure_dict(defaults.get("about"))

    paragraphs = about.get("paragraphs")
    if not isinstance(paragraphs, list) or len([p for p in paragraphs if has_text(p)]) == 0:
        about["paragraphs"] = about_defaults.get("paragraphs", [])
    else:
        about["paragraphs"] = paragraphs

    about["image"] = about.get("image", None)
    content["about"] = about

    # -------------------------
    # SERVICES
    # -------------------------
    services = _ensure_dict(content.get("services"))
    services_defaults = _ensure_dict(defaults.get("services"))

    if not has_text(services.get("title")):
        services["title"] = services_defaults.get("title", "Services")

    items = services.get("items")
    if not isinstance(items, list) or len(items) == 0:
        services["items"] = services_defaults.get("items", [])
    else:
        fixed = []
        for it in items[:6]:
            it = _ensure_dict(it)
            fixed.append({
                "title": it.get("title") if has_text(it.get("title")) else "Service",
                "description": it.get("description") if has_text(it.get("description")) else "Clear description of this service.",
                "image": it.get("image", None),
            })
        services["items"] = fixed

    content["services"] = services

    # -------------------------
    # TRUST
    # -------------------------
    trust = _ensure_dict(content.get("trust"))
    trust_defaults = _ensure_dict(defaults.get("trust"))

    items = trust.get("items")
    if not isinstance(items, list) or len([i for i in items if has_text(i)]) == 0:
        trust["items"] = trust_defaults.get("items", [])
    else:
        trust["items"] = items

    content["trust"] = trust

    # -------------------------
    # PROCESS
    # -------------------------
    process = _ensure_dict(content.get("process"))
    process_defaults = _ensure_dict(defaults.get("process"))

    steps = process.get("steps")
    if not isinstance(steps, list) or len(steps) == 0:
        process["steps"] = process_defaults.get("steps", [])
    else:
        fixed_steps = []
        for st in steps[:6]:
            st = _ensure_dict(st)
            fixed_steps.append({
                "title": st.get("title") if has_text(st.get("title")) else "Step",
                "description": st.get("description") if has_text(st.get("description")) else "Short explanation of this step.",
            })
        process["steps"] = fixed_steps

    content["process"] = process

    # -------------------------
    # TESTIMONIAL
    # -------------------------
    testimonial = _ensure_dict(content.get("testimonial"))
    testimonial_defaults = _ensure_dict(defaults.get("testimonial"))

    if not has_text(testimonial.get("quote")):
        testimonial["quote"] = testimonial_defaults.get("quote", "")
    if not has_text(testimonial.get("author")):
        testimonial["author"] = testimonial_defaults.get("author", "Customer")

    content["testimonial"] = testimonial

    # -------------------------
    # FAQ
    # -------------------------
    faq = _ensure_dict(content.get("faq"))
    faq_defaults = _ensure_dict(defaults.get("faq"))

    items = faq.get("items")
    if not isinstance(items, list) or len(items) == 0:
        faq["items"] = faq_defaults.get("items", [])
    else:
        fixed_faq = []
        for qa in items[:8]:
            qa = _ensure_dict(qa)
            fixed_faq.append({
                "q": qa.get("q") if has_text(qa.get("q")) else "Question?",
                "a": qa.get("a") if has_text(qa.get("a")) else "Clear helpful answer.",
            })
        faq["items"] = fixed_faq

    content["faq"] = faq

    # -------------------------
    # CTA
    # -------------------------
    cta = _ensure_dict(content.get("cta"))
    cta_defaults = _ensure_dict(defaults.get("cta"))

    if not has_text(cta.get("headline")):
        cta["headline"] = cta_defaults.get("headline", "")
    if not has_text(cta.get("subheadline")):
        cta["subheadline"] = cta_defaults.get("subheadline", "")
    if not has_text(cta.get("button")):
        cta["button"] = cta_defaults.get("button", "Get started")

    content["cta"] = cta

    # -------------------------
    # GALLERY
    # -------------------------
    gallery = _ensure_dict(content.get("gallery"))
    gallery["images"] = gallery.get("images", [])
    content["gallery"] = gallery

    # -------------------------
    # CONTACT
    # -------------------------
    contact = _ensure_dict(content.get("contact"))
    contact_defaults = _ensure_dict(defaults.get("contact"))

    for k in ["phone", "email", "address"]:
        contact[k] = contact.get(k) or contact_defaults.get(k, "")

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

def _is_empty_value(v) -> bool:
    if v is None:
        return True
    if isinstance(v, str) and not v.strip():
        return True
    if isinstance(v, (list, tuple, dict)) and len(v) == 0:
        return True
    return False


def _deep_merge_defaults(defaults: dict, incoming: dict) -> dict:
    """
    Deep merge where `incoming` overrides `defaults` ONLY when it has a real value.
    - Keeps all keys from defaults
    - Uses incoming values when present and non-empty
    - Recursively merges dicts
    """
    if not isinstance(defaults, dict):
        return incoming if not _is_empty_value(incoming) else defaults

    out = dict(defaults)

    if not isinstance(incoming, dict):
        return out

    for k, v in incoming.items():
        if k not in out:
            # accept new keys from incoming if they aren't empty
            if not _is_empty_value(v):
                out[k] = v
            continue

        dv = out.get(k)

        # recurse dicts
        if isinstance(dv, dict) and isinstance(v, dict):
            out[k] = _deep_merge_defaults(dv, v)
            continue

        # merge lists: if incoming list has items, use it; else keep default
        if isinstance(dv, list) and isinstance(v, list):
            out[k] = v if len(v) > 0 else dv
            continue

        # normal scalar: only override if incoming is not empty
        if not _is_empty_value(v):
            out[k] = v

    return out


def _normalize_full_content(ai: dict, defaults: dict) -> dict:
    """
    Guarantees the final content has a full schema:
    - start with defaults (complete)
    - merge AI (partial)
    - ensure required containers exist
    """
    ai = ai if isinstance(ai, dict) else {}
    defaults = defaults if isinstance(defaults, dict) else {}

    merged = _deep_merge_defaults(defaults, ai)

    # hard guarantees for containers your frontend expects
    if "hero" not in merged or not isinstance(merged["hero"], dict):
        merged["hero"] = {}
    if "about" not in merged or not isinstance(merged["about"], dict):
        merged["about"] = {}
    if "contact" not in merged or not isinstance(merged["contact"], dict):
        merged["contact"] = {}
    if "location" not in merged or not isinstance(merged["location"], dict):
        merged["location"] = {}

    # ensure about paragraphs is a list
    ap = merged["about"].get("paragraphs")
    if not isinstance(ap, list):
        merged["about"]["paragraphs"] = []

    return merged



# =========================
# DEFAULTS (FULL BUILDER COVERAGE)
# =========================

def build_default_content(template: str, ai_input: dict, username: str) -> dict:
    """
    Deterministic fallback if OpenAI is missing/fails.
    IMPORTANT: Must NOT include placeholders like 'Your Business Name'.
    """
    biz_type = (template or ai_input.get("business_type") or "business").lower()
    city = _clean_text(ai_input.get("city")) or ""
    goal = _clean_text(ai_input.get("primary_goal")) or "Get started"

    name = username.replace("-", " ").title()

    # A little type-specific flavor so every site isn't identical
    if biz_type == "restaurant":
        sub = "Fresh food, warm atmosphere, and simple online booking."
        services = [
            {"title": "Dine-in", "description": "A comfortable space with great service.", "image": None},
            {"title": "Takeaway", "description": "Order ahead and pick up fast.", "image": None},
            {"title": "Catering", "description": "Events, groups, and special occasions.", "image": None},
        ]
        trust = ["Fresh ingredients", "Fast service", "Loved by locals"]
        cta_head = "Want a table?"
        cta_sub = "Book in seconds — we’ll confirm quickly."
        cta_btn = "Book now"
    elif biz_type == "fitness":
        sub = "Coaching that builds strength, confidence, and consistency."
        services = [
            {"title": "1:1 Coaching", "description": "Personal training tailored to your goals.", "image": None},
            {"title": "Programs", "description": "Structured plans you can follow weekly.", "image": None},
            {"title": "Nutrition", "description": "Simple guidance that’s easy to stick to.", "image": None},
        ]
        trust = ["Results-driven", "Friendly coaching", "Clear plan"]
        cta_head = "Ready to start?"
        cta_sub = "Send a message — we’ll recommend the best next step."
        cta_btn = "Get started"
    elif biz_type == "agency":
        sub = "Modern marketing that turns attention into customers."
        services = [
            {"title": "Paid Ads", "description": "Launch campaigns that convert.", "image": None},
            {"title": "Content", "description": "Posts & creatives built for growth.", "image": None},
            {"title": "Landing Pages", "description": "Simple pages that capture leads.", "image": None},
        ]
        trust = ["Fast turnaround", "Clear strategy", "Conversion-first"]
        cta_head = "Want more leads?"
        cta_sub = "Tell us what you sell — we’ll map the fastest path."
        cta_btn = "Get a plan"
    else:
        sub = "A modern website that turns visitors into customers."
        services = [
            {"title": "Consultation", "description": "Clear advice tailored to your needs.", "image": None},
            {"title": "Delivery", "description": "Fast execution and reliable results.", "image": None},
            {"title": "Support", "description": "We’re here when you need us.", "image": None},
        ]
        trust = ["Clear pricing", "Fast response", "Trusted quality"]
        cta_head = "Ready to take the next step?"
        cta_sub = "Send a message — we respond quickly."
        cta_btn = goal or "Get started"

    return {
        "business_name": name,
        "hero": {
            "headline": name,
            "subheadline": sub + (f" Serving {city}." if city else ""),
            "cta_text": goal or cta_btn,
            "image": None,
        },
        "highlight": {
            "headline": "Make a strong first impression.",
            "subheadline": "Warm, trustworthy design — plus real copy customers understand.",
        },
        "about": {
            "paragraphs": [
                "We focus on clarity, quality, and a great customer experience.",
                "Everything here is editable — change the wording, images, and sections anytime.",
            ],
            "image": None,
        },
        "services": {
            "title": "Services",
            "items": services,
        },
        "trust": {"items": trust},
        "process": {
            "steps": [
                {"title": "Reach out", "description": "Send a message with what you need."},
                {"title": "Get a plan", "description": "We reply with a simple next step."},
                {"title": "Get results", "description": "We deliver quickly — and you can edit anytime."},
            ]
        },
        "testimonial": {
            "quote": "“Professional, fast, and easy to work with.”",
            "author": "Happy customer",
        },
        "faq": {
            "items": [
                {"q": "How fast can I get started?", "a": "Usually the same day. Send a message and we’ll take it from there."},
                {"q": "Can I change anything later?", "a": "Yes — you can edit everything and it autosaves."},
                {"q": "Do I need images?", "a": "No. But adding real photos increases trust and conversions."},
            ]
        },
        "gallery": {"images": []},
        "cta": {"headline": cta_head, "subheadline": cta_sub, "button": cta_btn},
        "contact": {"phone": "", "email": "", "address": ""},
        "location": {"city": city},
        "_builder": {"tone": "warm", "sections": None, "hidden": []},
    }



# =========================
# OPENAI GENERATION (FULL BUILDER COVERAGE)
# =========================

def ai_generate_content_with_openai(template: str, ai_input: dict, username: str) -> Optional[dict]:
    """
    Returns a FULL content_json object that matches what your frontend renderer expects.
    If OpenAI fails or is not configured, return None (so caller can fallback).
    """
    if not _openai_client:
        return None

    biz_type = (template or ai_input.get("business_type") or "business").lower()
    raw_prompt = _clean_text(ai_input.get("raw_prompt")) or ""
    city = _clean_text(ai_input.get("city")) or ""
    inferred_goal = _clean_text(ai_input.get("primary_goal")) or "Get started"

    # Make a decent default business name from username if model doesn't provide one
    fallback_name = username.replace("-", " ").title()

    system = (
        "You generate website copy as strict JSON only.\n"
        "Return ONLY valid JSON. No markdown. No commentary.\n"
        "Keep copy realistic, specific, and short.\n"
        "Avoid placeholders like 'Your Business Name'.\n"
        "If info is missing, creatively infer plausible details from the prompt.\n"
    )

    user = f"""
Business prompt:
{raw_prompt}

Business type: {biz_type}
City (if mentioned): {city}
Primary goal CTA: {inferred_goal}

Return JSON with EXACT keys (match this schema):
{{
  "business_name": "...",
  "hero": {{
    "headline": "...",
    "subheadline": "...",
    "cta_text": "..."
  }},
  "highlight": {{
    "headline": "...",
    "subheadline": "..."
  }},
  "about": {{
    "paragraphs": ["...", "..."],
    "image": null
  }},
  "services": {{
    "title": "Services",
    "items": [
      {{"title": "...", "description": "...", "image": null}},
      {{"title": "...", "description": "...", "image": null}},
      {{"title": "...", "description": "...", "image": null}}
    ]
  }},
  "trust": {{
    "items": ["...", "...", "..."]
  }},
  "process": {{
    "steps": [
      {{"title": "...", "description": "..."}},
      {{"title": "...", "description": "..."}},
      {{"title": "...", "description": "..."}}
    ]
  }},
  "testimonial": {{
    "quote": "“...”",
    "author": "..."
  }},
  "faq": {{
    "items": [
      {{"q": "...", "a": "..."}},
      {{"q": "...", "a": "..."}},
      {{"q": "...", "a": "..."}}
    ]
  }},
  "gallery": {{
    "images": []
  }},
  "cta": {{
    "headline": "...",
    "subheadline": "...",
    "button": "..."
  }},
  "contact": {{
    "phone": "",
    "email": "",
    "address": ""
  }},
  "location": {{
    "city": "{city}"
  }},
  "_builder": {{
    "tone": "warm",
    "sections": null,
    "hidden": []
  }}
}}

Rules:
- business_name must be a real-looking name (NOT "Your Business Name"). If unsure, use "{fallback_name}".
- hero.headline should usually be the business_name or a strong value prop.
- hero.subheadline should describe WHAT they do in plain language.
- services must be specific to the prompt.
- If city exists, use it naturally in copy (don’t spam it).
"""

    try:
        # Use responses that work with your OpenAI client import
        # (your file already sets _openai_client = OpenAI(...))
        resp = _openai_client.chat.completions.create(
            model=os.getenv("OPENAI_WEBSITE_MODEL", "gpt-4o-mini"),
            temperature=0.75,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )

        text = (resp.choices[0].message.content or "").strip()
        if not text:
            return None

        data = json.loads(text)

        # Hard safety: ensure required keys exist (so frontend doesn't fallback)
        if not isinstance(data, dict):
            return None

        # Minimal normalization so "services" always works with your renderer
        if "services" in data and isinstance(data["services"], dict):
            items = data["services"].get("items")
            if not isinstance(items, list):
                data["services"]["items"] = []
            else:
                # Ensure each item has title/description/image keys
                fixed_items = []
                for it in items[:9]:
                    if not isinstance(it, dict):
                        continue
                    fixed_items.append({
                        "title": _clean_text(it.get("title")) or "Service",
                        "description": _clean_text(it.get("description")) or "Short description of this service.",
                        "image": it.get("image") if isinstance(it.get("image"), str) else None,
                    })
                data["services"]["items"] = fixed_items

        # Default business_name if missing (prevents "Your Business Name" fallback)
        if not _clean_text(data.get("business_name")):
            data["business_name"] = fallback_name

        # Default hero bits if missing
        data.setdefault("hero", {})
        if not _clean_text(data["hero"].get("headline")):
            data["hero"]["headline"] = data["business_name"]
        if not _clean_text(data["hero"].get("subheadline")):
            data["hero"]["subheadline"] = "A professional service you can trust."
        if not _clean_text(data["hero"].get("cta_text")):
            data["hero"]["cta_text"] = inferred_goal or "Get started"
        if "image" not in data["hero"]:
            data["hero"]["image"] = None

        # Ensure builder meta exists so tone UI can be meaningful later
        data.setdefault("_builder", {})
        data["_builder"].setdefault("tone", "warm")
        data["_builder"].setdefault("sections", None)
        data["_builder"].setdefault("hidden", [])

        return data

    except Exception as e:
        print("OpenAI content generation failed:", str(e))
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

    # -------------------------
    # HARD LIMIT: 1 SITE / USER
    # -------------------------
    if db.query(Website).filter(Website.user_id == user.id).count() >= 1:
        raise HTTPException(status_code=403, detail="Only one website allowed")

    username = (payload.get("username") or "").strip().lower()
    prompt = (payload.get("prompt") or "").strip()

    if not username:
        raise HTTPException(status_code=400, detail="Missing username")

    if db.query(Website).filter(Website.username == username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    # -------------------------
    # INFER AI INPUT
    # -------------------------
    ai_input = infer_ai_input_from_prompt(prompt)
    template = ai_input.get("business_type", "business")

    # -------------------------
    # PLAN → PAGE LIMITS
    # -------------------------
    max_pages = 3 if plan == "pro" else 1

    # -------------------------
    # AI STRUCTURE (LAYOUT)
    # -------------------------
    structure = generate_ai_structure(
        business_type=template,
        goal=_clean_text(ai_input.get("primary_goal")) or "conversions",
        version=1,
    )

    structure["plan"] = {
        "name": plan,
        "max_pages": max_pages,
        "can_publish": plan in ("starter", "pro"),
    }

    # =====================================================
    # 🔥 CONTENT GENERATION (THIS WAS THE BROKEN PART)
    # =====================================================

    # 1️⃣ ALWAYS build strong defaults FIRST (full schema)
    defaults = build_default_content(
        template=template,
        ai_input=ai_input,
        username=username,
    )

    # 2️⃣ TRY OpenAI (may return partial JSON or None)
    ai_content = ai_generate_content_with_openai(
        template=template,
        ai_input=ai_input,
        username=username,
    )

    # 3️⃣ MERGE: defaults → AI (AI WINS, defaults fill gaps)
    content = _normalize_full_content(
        ai=ai_content or {},
        defaults=defaults,
    )

    # -------------------------
    # PUBLISH STATUS
    # -------------------------
    publish_status = "published" if plan in ("starter", "pro") else "draft"

    # -------------------------
    # SAVE WEBSITE
    # -------------------------
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
