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
