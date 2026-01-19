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


def _normalize_full_content(ai: dict, defaults: dict) -> dict:
    """
    Merge defaults -> ai (ai wins), but force modern schema and remove placeholders.
    """
    base = defaults if isinstance(defaults, dict) else {}
    patch = ai if isinstance(ai, dict) else {}

    # shallow merge for top-level
    out = {**base, **patch}

    # Ensure business_name
    if not _clean_text(out.get("business_name")):
        out["business_name"] = _clean_text(base.get("business_name")) or "Business"

    # HERO
    out.setdefault("hero", {})
    if not isinstance(out["hero"], dict):
        out["hero"] = {}
    out["hero"].setdefault("headline", out["business_name"])
    out["hero"].setdefault("subheadline", base.get("hero", {}).get("subheadline", "A modern website that turns visitors into customers."))
    out["hero"].setdefault("cta_text", base.get("hero", {}).get("cta_text", "Get started"))
    if "image" not in out["hero"]:
        out["hero"]["image"] = None

    # Kill classic placeholders if they slip in
    if _clean_text(out["hero"].get("headline")).lower() in ["your business name", "your business"]:
        out["hero"]["headline"] = out["business_name"]
    if _clean_text(out["hero"].get("subheadline")).lower() in ["short description of what you do", "short description of what you do."]:
        out["hero"]["subheadline"] = base.get("hero", {}).get("subheadline", "A modern website that turns visitors into customers.")

    # ABOUT (modern paragraphs array)
    out.setdefault("about", {})
    if not isinstance(out["about"], dict):
        out["about"] = {}
    paragraphs = out["about"].get("paragraphs")
    if not isinstance(paragraphs, list) or len([p for p in paragraphs if _clean_text(p)]) < 2:
        out["about"]["paragraphs"] = base.get("about", {}).get("paragraphs", [
            f"At {out['business_name']}, we help customers with fast, reliable service.",
            "We focus on clarity, quality, and a great customer experience.",
        ])
    if "image" not in out["about"]:
        out["about"]["image"] = None

    # HIGHLIGHT
    out.setdefault("highlight", {})
    if not isinstance(out["highlight"], dict):
        out["highlight"] = {}
    out["highlight"].setdefault("headline", base.get("highlight", {}).get("headline", "Make a strong first impression."))
    out["highlight"].setdefault("subheadline", base.get("highlight", {}).get("subheadline", "Clear messaging + a premium layout that drives action."))

    # SERVICES
    out.setdefault("services", {})
    if not isinstance(out["services"], dict):
        out["services"] = {}
    out["services"].setdefault("title", base.get("services", {}).get("title", "Services"))
    items = out["services"].get("items")
    if not isinstance(items, list) or len(items) < 3:
        out["services"]["items"] = base.get("services", {}).get("items", [])
    # normalize service items
    fixed = []
    for it in (out["services"].get("items") or [])[:9]:
        if not isinstance(it, dict):
            continue
        fixed.append({
            "title": _clean_text(it.get("title")) or "Service",
            "description": _clean_text(it.get("description")) or "Describe your service clearly and simply.",
            "image": it.get("image") if isinstance(it.get("image"), str) else None,
        })
    out["services"]["items"] = fixed if fixed else base.get("services", {}).get("items", [])

    # TRUST
    out.setdefault("trust", {})
    if not isinstance(out["trust"], dict):
        out["trust"] = {}
    trust_items = out["trust"].get("items")
    if not isinstance(trust_items, list) or len([x for x in trust_items if _clean_text(x)]) < 3:
        out["trust"]["items"] = base.get("trust", {}).get("items", ["Clear pricing", "Fast response", "Trusted quality"])

    # PROCESS
    out.setdefault("process", {})
    if not isinstance(out["process"], dict):
        out["process"] = {}
    steps = out["process"].get("steps")
    if not isinstance(steps, list) or len(steps) < 3:
        out["process"]["steps"] = base.get("process", {}).get("steps", [])

    # TESTIMONIAL
    out.setdefault("testimonial", {})
    if not isinstance(out["testimonial"], dict):
        out["testimonial"] = {}
    out["testimonial"].setdefault("quote", base.get("testimonial", {}).get("quote", "“Professional, fast, and easy to work with.”"))
    out["testimonial"].setdefault("author", base.get("testimonial", {}).get("author", "Happy customer"))

    # FAQ
    out.setdefault("faq", {})
    if not isinstance(out["faq"], dict):
        out["faq"] = {}
    faq_items = out["faq"].get("items")
    if not isinstance(faq_items, list) or len(faq_items) < 3:
        out["faq"]["items"] = base.get("faq", {}).get("items", [])

    # CTA
    out.setdefault("cta", {})
    if not isinstance(out["cta"], dict):
        out["cta"] = {}
    out["cta"].setdefault("headline", base.get("cta", {}).get("headline", "Ready to take the next step?"))
    out["cta"].setdefault("subheadline", base.get("cta", {}).get("subheadline", "Send a message — we respond quickly."))
    out["cta"].setdefault("button", base.get("cta", {}).get("button", out["hero"].get("cta_text", "Get started")))

    # Gallery
    out.setdefault("gallery", {})
    if not isinstance(out["gallery"], dict):
        out["gallery"] = {}
    if not isinstance(out["gallery"].get("images"), list):
        out["gallery"]["images"] = []

    # Contact + location
    out.setdefault("contact", {})
    if not isinstance(out["contact"], dict):
        out["contact"] = {}
    out["contact"].setdefault("phone", "")
    out["contact"].setdefault("email", "")
    out["contact"].setdefault("address", "")

    out.setdefault("location", {})
    if not isinstance(out["location"], dict):
        out["location"] = {}
    out["location"].setdefault("city", _clean_text(base.get("location", {}).get("city")))

    # Builder meta
    out.setdefault("_builder", {})
    if not isinstance(out["_builder"], dict):
        out["_builder"] = {}
    out["_builder"].setdefault("tone", "warm")
    out["_builder"].setdefault("sections", None)
    out["_builder"].setdefault("hidden", [])

    return out


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
    Returns a FULL, AIWebsiteRenderer-compatible content object (modern schema).
    Never returns placeholders like 'Your Business Name'.
    """
    raw_prompt = _clean_text(ai_input.get("raw_prompt")) or ""
    city = _clean_text(ai_input.get("city")) or ""
    goal = _clean_text(ai_input.get("primary_goal")) or "Get started"

    business_name = username.replace("-", " ").title()
    if raw_prompt:
        # light attempt to derive a nicer name from prompt (optional)
        # keep it safe; never produce generic placeholders
        pass

    # Simple “what you do” seed
    what = ""
    if raw_prompt:
        what = raw_prompt.strip()
        if len(what) > 120:
            what = what[:120].rstrip() + "…"

    headline = business_name
    subheadline = (
        (f"{what}." if what else "A modern website that turns visitors into customers.")
        + (f" Serving {city}." if city else "")
    ).strip()

    return {
        "business_name": business_name,
        "hero": {
            "headline": headline,
            "subheadline": subheadline,
            "cta_text": goal,
            "image": None,
        },
        "highlight": {
            "headline": "Make a strong first impression.",
            "subheadline": "Clear messaging + a premium layout that drives action.",
        },
        "about": {
            "paragraphs": [
                f"At {business_name}, we help customers with fast, reliable service.",
                "We focus on clarity, quality, and a great customer experience.",
            ],
            "image": None,
        },
        "services": {
            "title": "Services",
            "items": [
                {"title": "Primary service", "description": "Describe your main offer clearly and simply.", "image": None},
                {"title": "Second service", "description": "Another high-value service your customers want.", "image": None},
                {"title": "Support", "description": "Fast response and clear communication.", "image": None},
            ],
        },
        "trust": {
            "items": ["Clear pricing", "Fast response", "Trusted quality"],
        },
        "process": {
            "steps": [
                {"title": "Reach out", "description": "Send a quick message with what you need."},
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
        "cta": {
            "headline": "Ready to take the next step?",
            "subheadline": "Send a message — we respond quickly.",
            "button": goal,
        },
        "contact": {"phone": "", "email": "", "address": ""},
        "location": {"city": city},
        "_builder": {
            "tone": "warm",
            "sections": None,
            "hidden": [],
        },
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
    print("=== [AUTOPILOTAI] /api/dashboard/websites/create HIT ===")

    plan = (user.subscription_plan or "free").lower()

    # 1 site per user
    if db.query(Website).filter(Website.user_id == user.id).count() >= 1:
        raise HTTPException(status_code=403, detail="Only one website allowed")

    username = (payload.get("username") or "").strip().lower()
    prompt = (payload.get("prompt") or "").strip()

    if not username:
        raise HTTPException(status_code=400, detail="Missing username")

    if db.query(Website).filter(Website.username == username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    # --- HARD REQUIRE: AI must be configured ---
    if not _openai_client:
        print("=== [AUTOPILOTAI] OPENAI CLIENT NOT CONFIGURED (missing import or OPENAI_API_KEY) ===")
        raise HTTPException(
            status_code=500,
            detail="OpenAI not configured on server (OPENAI_API_KEY missing or OpenAI client failed to init).",
        )

    ai_input = infer_ai_input_from_prompt(prompt)
    template = (ai_input.get("business_type") or "business").lower()

    max_pages = 3 if plan == "pro" else 1

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

    # Defaults (modern schema)
    defaults = build_default_content(template=template, ai_input=ai_input, username=username)

    # --- MUST CALL AI ---
    print("=== [AUTOPILOTAI] CALLING OPENAI FOR WEBSITE CONTENT ===")
    ai_content = ai_generate_content_with_openai(template=template, ai_input=ai_input, username=username)

    if not isinstance(ai_content, dict) or len(ai_content.keys()) == 0:
        print("=== [AUTOPILOTAI] OPENAI RETURNED EMPTY/INVALID JSON ===")
        raise HTTPException(status_code=500, detail="AI generation failed: empty/invalid JSON response.")

    # Merge + normalize
    content = _normalize_full_content(ai=ai_content, defaults=defaults)

    # --- HARD BLOCK: prevent classic placeholders from ever being saved ---
    def _contains_placeholders(obj: Any) -> bool:
        bad = {
            "your business name",
            "short description of what you do",
            "write a short introduction about your business here.",
            "service one",
            "service two",
            "service three",
        }

        def walk(x: Any) -> bool:
            if isinstance(x, dict):
                return any(walk(v) for v in x.values())
            if isinstance(x, list):
                return any(walk(v) for v in x)
            if isinstance(x, str):
                s = x.strip().lower()
                return s in bad
            return False

        return walk(obj)

    if _contains_placeholders(content):
        print("=== [AUTOPILOTAI] PLACEHOLDERS DETECTED - BLOCKING SAVE ===")
        raise HTTPException(status_code=500, detail="AI output still contains placeholders; blocking save.")

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

    print("=== [AUTOPILOTAI] WEBSITE CREATED OK ===", username)

    return {
        "ok": True,
        "username": username,
        "redirect": f"/r/{username}?edit=1",
        "plan": plan,
        "max_pages": max_pages,
        "published": plan in ("starter", "pro"),
        "debug_has_ai": True,
        "debug_business_name": content.get("business_name"),
        "debug_hero_headline": (content.get("hero") or {}).get("headline"),
    }
