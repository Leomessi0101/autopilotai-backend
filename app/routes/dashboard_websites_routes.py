from fastapi import APIRouter, HTTPException, Depends, Body
from sqlalchemy.orm import Session
import json
import re
import os
from typing import Optional, Any, Dict, List
import hashlib
import base64

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

def ai_generate_content_with_openai(
    template: str,
    ai_input: dict,
    username: str,
    allowed_sections: list[str] | None = None,
) -> Optional[dict]:
    """
    Generates AI website content ONLY for the allowed sections.
    If allowed_sections is None, falls back to full generation.
    """
    if not _openai_client:
        return None

    biz_type = (template or ai_input.get("business_type") or "business").lower()
    raw_prompt = _clean_text(ai_input.get("raw_prompt")) or ""
    city = _clean_text(ai_input.get("city")) or ""
    inferred_goal = _clean_text(ai_input.get("primary_goal")) or "Get started"

    allowed = set(allowed_sections or [])

    fallback_name = username.replace("-", " ").title()

    # -------------------------
    # SYSTEM PROMPT
    # -------------------------
    system = (
        "You generate website copy as strict JSON only.\n"
        "Return ONLY valid JSON. No markdown. No commentary.\n"
        "Generate content ONLY for the sections explicitly requested.\n"
        "Do NOT invent extra sections.\n"
        "Keep copy realistic, specific, and concise.\n"
        "Avoid placeholders like 'Your Business Name'.\n"
    )

    # -------------------------
    # DYNAMIC SCHEMA (BASED ON SECTIONS)
    # -------------------------
    section_schema = {}

    if "hero" in allowed:
        section_schema["hero"] = {
            "headline": "...",
            "subheadline": "...",
            "cta_text": "...",
        }

    if "highlight" in allowed:
        section_schema["highlight"] = {
            "headline": "...",
            "subheadline": "...",
        }

    if "about" in allowed:
        section_schema["about"] = {
            "paragraphs": ["...", "..."],
            "image": None,
        }

    if "services" in allowed:
        section_schema["services"] = {
            "title": "Services",
            "items": [
                {"title": "...", "description": "...", "image": None},
                {"title": "...", "description": "...", "image": None},
                {"title": "...", "description": "...", "image": None},
            ],
        }

    if "trust" in allowed:
        section_schema["trust"] = {
            "items": ["...", "...", "..."],
        }

    if "process" in allowed:
        section_schema["process"] = {
            "steps": [
                {"title": "...", "description": "..."},
                {"title": "...", "description": "..."},
                {"title": "...", "description": "..."},
            ],
        }

    if "testimonial" in allowed:
        section_schema["testimonial"] = {
            "quote": "“...”",
            "author": "...",
        }

    if "faq" in allowed:
        section_schema["faq"] = {
            "items": [
                {"q": "...", "a": "..."},
                {"q": "...", "a": "..."},
                {"q": "...", "a": "..."},
            ],
        }

    if "gallery" in allowed:
        section_schema["gallery"] = {
            "images": [],
        }

    if "cta" in allowed:
        section_schema["cta"] = {
            "headline": "...",
            "subheadline": "...",
            "button": "...",
        }

    if "contact" in allowed:
        section_schema["contact"] = {
            "phone": "",
            "email": "",
            "address": "",
        }

    if "location" in allowed:
        section_schema["location"] = {
            "city": city,
        }

    # -------------------------
    # USER PROMPT
    # -------------------------
    user = f"""
Business prompt:
{raw_prompt}

Business type: {biz_type}
City (if mentioned): {city}
Primary goal CTA: {inferred_goal}

Allowed sections:
{sorted(list(allowed))}

Return JSON with EXACT keys:
{{
  "business_name": "...",
  {json.dumps(section_schema, indent=2)}
}}

Rules:
- Generate ONLY the allowed sections.
- business_name must be real (use "{fallback_name}" if unsure).
- Be specific to the business prompt.
- Do NOT include sections not listed above.
"""

    try:
        resp = _openai_client.chat.completions.create(
            model=os.getenv("OPENAI_WEBSITE_MODEL", "gpt-4o-mini"),
            temperature=0.7,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )

        text = (resp.choices[0].message.content or "").strip()
        if not text:
            return None

        data = json.loads(text)
        if not isinstance(data, dict):
            return None

        # -------------------------
        # HARD FILTER: REMOVE UNALLOWED SECTIONS
        # -------------------------
        cleaned = {
            k: v
            for k, v in data.items()
            if k == "business_name" or k in allowed
        }

        if not _clean_text(cleaned.get("business_name")):
            cleaned["business_name"] = fallback_name

        cleaned["_builder"] = {
            "tone": "warm",
            "sections": list(allowed),
            "hidden": [],
        }

        return cleaned

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
    ai_content = ai_generate_content_with_openai(
        template,
        ai_input,
        username,
        allowed_sections=structure.get("sections", []),
    )
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

# =========================
# CUSTOM DOMAIN (CONNECT + VERIFY)
# =========================

def _normalize_host(host: str) -> str:
    h = (host or "").strip().lower()
    if ":" in h:
        h = h.split(":", 1)[0]
    if h.startswith("www."):
        h = h[4:]
    return h

def _domain_token_for_site(site: Website) -> str:
    """
    Deterministic token (no DB column needed).
    User adds TXT record:
      autopilotai-verify=<token>
    """
    raw = f"autopilotai:{site.id}:{site.user_id}:{site.username}"
    digest = hashlib.sha256(raw.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")[:32]

@router.get("/{username}/domain/status")
def domain_status(
    username: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    site = db.query(Website).filter(Website.username == username).first()
    if not site:
        raise HTTPException(status_code=404, detail="Website not found")
    if site.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    token = _domain_token_for_site(site)
    return {
        "ok": True,
        "custom_domain": site.custom_domain,
        "domain_verified": bool(site.domain_verified),
        "txt_name": "@",
        "txt_value": f"autopilotai-verify={token}",
    }

@router.post("/{username}/domain/set")
def set_custom_domain(
    username: str,
    payload: dict = Body(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    site = db.query(Website).filter(Website.username == username).first()
    if not site:
        raise HTTPException(status_code=404, detail="Website not found")
    if site.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    domain = _normalize_host(payload.get("domain") or "")
    if not domain:
        raise HTTPException(status_code=400, detail="Missing domain")

    existing = db.query(Website).filter(Website.custom_domain == domain).first()
    if existing and existing.id != site.id:
        raise HTTPException(status_code=400, detail="Domain already in use")

    site.custom_domain = domain
    site.domain_verified = False
    db.commit()

    token = _domain_token_for_site(site)
    return {
        "ok": True,
        "custom_domain": site.custom_domain,
        "domain_verified": bool(site.domain_verified),
        "txt_name": "@",
        "txt_value": f"autopilotai-verify={token}",
        "next": "Add TXT record, then call /verify",
    }

@router.post("/{username}/domain/verify")
def verify_custom_domain(
    username: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    site = db.query(Website).filter(Website.username == username).first()
    if not site:
        raise HTTPException(status_code=404, detail="Website not found")
    if site.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    if not site.custom_domain:
        raise HTTPException(status_code=400, detail="No custom_domain set")

    token = _domain_token_for_site(site)
    expected = f"autopilotai-verify={token}"

    try:
        import dns.resolver  # type: ignore
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="dnspython missing. Install with: pip install dnspython",
        )

    try:
        answers = dns.resolver.resolve(site.custom_domain, "TXT")
        values = []
        for rdata in answers:
            parts = []
            for s in getattr(rdata, "strings", []):
                try:
                    parts.append(s.decode("utf-8"))
                except Exception:
                    pass
            txt = "".join(parts).strip()
            if txt:
                values.append(txt)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"TXT lookup failed: {str(e)}")

    if expected not in values:
        raise HTTPException(
            status_code=400,
            detail=f"TXT not found. Expected: {expected}",
        )

    site.domain_verified = True
    db.commit()

    return {"ok": True, "custom_domain": site.custom_domain, "domain_verified": True}
