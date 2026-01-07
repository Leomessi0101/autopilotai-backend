from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Literal, Optional
from app.utils.auth import get_current_user
from app.database.session import SessionLocal
from app.utils.usage import get_user_limit, reset_if_new_month
from app.database.models import SavedContent
from openai import OpenAI
import os
import re

router = APIRouter()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class GrowthPackRequest(BaseModel):
    prompt: str
    generate_image: bool = False  # paid-only


class RegenerateSectionRequest(BaseModel):
    prompt: str
    section: Literal["social", "email", "ads"]
    generate_image: bool = False  # only relevant for ads (paid-only)


def _extract_sections(text: str):
    """
    Expects strict markers:
    === SOCIAL POSTS ===
    ...
    === EMAIL ===
    ...
    === ADS ===
    ...
    """
    def grab(label: str):
        if label not in text:
            return ""
        after = text.split(label, 1)[1]
        # split on next "=== ... ===" marker if present
        parts = re.split(r"\n\s*===\s*[A-Z ]+\s*===\s*\n", after, maxsplit=1)
        return (parts[0] or "").strip()

    social = grab("=== SOCIAL POSTS ===")
    email = grab("=== EMAIL ===")
    ads = grab("=== ADS ===")
    return social, email, ads


def _check_and_consume_once(db, user):
    reset_if_new_month(user)

    limit = get_user_limit(user.subscription_plan)
    used = user.used_generations or 0

    if limit is not None and used >= limit:
        raise HTTPException(
            status_code=403,
            detail="Monthly generation limit reached. Please upgrade."
        )

    user.used_generations = (user.used_generations or 0) + 1
    db.add(user)
    db.commit()


def _is_paid(user) -> bool:
    return bool(user.subscription_plan) and user.subscription_plan.lower() != "free"


@router.post("/growth-pack/generate")
def generate_growth_pack(
    data: GrowthPackRequest,
    user=Depends(get_current_user)
):
    db = SessionLocal()
    try:
        if not data.prompt or not data.prompt.strip():
            raise HTTPException(status_code=400, detail="Prompt is required")

        # Charge exactly ONCE for the whole pack
        _check_and_consume_once(db, user)

        # Premium-quality system prompt (stronger + stricter)
        system = (
            "You are a world-class direct response marketer and brand copywriter.\n"
            "Output ONLY the content. NO explanations.\n"
            "Follow the format EXACTLY with these section markers.\n\n"
            "FORMAT STRICTLY:\n"
            "=== SOCIAL POSTS ===\n"
            "Write EXACTLY 5 posts. Make them high-signal, non-generic, and conversion-aware.\n"
            "Use strong hooks, clear value, and a natural CTA.\n\n"
            "=== EMAIL ===\n"
            "Write ONE send-ready business email in this structure:\n"
            "Subject: ...\n"
            "<body>\n"
            "Professional, human, confident. No hype.\n\n"
            "=== ADS ===\n"
            "Write EXACTLY 3 ads in this structure:\n"
            "AD 1:\nHeadline:\nPrimary text:\nCTA:\n\n"
            "AD 2:\nHeadline:\nPrimary text:\nCTA:\n\n"
            "AD 3:\nHeadline:\nPrimary text:\nCTA:\n"
            "Make the ads punchy and specific.\n"
        )

        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": data.prompt},
            ]
        )

        output = (resp.choices[0].message.content or "").strip()
        if not output:
            raise HTTPException(500, "Empty AI response")

        social, email, ads = _extract_sections(output)

        # Save: one grouped item + also per-section (so My Work can show them cleanly later)
        db.add(SavedContent(
            user_id=user.id,
            content_type="growth_pack",
            prompt=data.prompt,
            result=output
        ))
        db.add(SavedContent(
            user_id=user.id,
            content_type="growth_pack_social",
            prompt=data.prompt,
            result=social or ""
        ))
        db.add(SavedContent(
            user_id=user.id,
            content_type="growth_pack_email",
            prompt=data.prompt,
            result=email or ""
        ))
        db.add(SavedContent(
            user_id=user.id,
            content_type="growth_pack_ads",
            prompt=data.prompt,
            result=ads or ""
        ))
        db.commit()

        image_url: Optional[str] = None

        # Optional paid image (ads-focused)
        if data.generate_image:
            if not _is_paid(user):
                # do NOT error; just return notice
                return {
                    "content": social,
                    "email": email,
                    "ads": ads,
                    "image": None,
                    "error": "AI Image is only available for paid users. Upgrade to unlock images."
                }

            visual_prompt = f"""
Create a high-quality, visually engaging marketing image.
NO TEXT IN THE IMAGE.
Modern, premium SaaS marketing look.

AD CONTEXT (for inspiration):
{(ads or output)[:900]}
"""

            img = client.images.generate(
                model="gpt-image-1",
                prompt=visual_prompt,
                size="1024x1024",
                response_format="url"
            )

            try:
                image_url = img.data[0].url
            except:
                try:
                    b64 = img.data[0].b64_json
                    image_url = f"data:image/png;base64,{b64}"
                except:
                    image_url = None

        return {
            "content": social,
            "email": email,
            "ads": ads,
            "image": image_url,
            "error": None
        }

    except HTTPException:
        raise
    except Exception as e:
        # Keep it simple; Render logs will show the full traceback
        raise HTTPException(status_code=500, detail=f"Growth Pack error: {str(e)}")
    finally:
        db.close()


@router.post("/growth-pack/regenerate")
def regenerate_growth_pack_section(
    data: RegenerateSectionRequest,
    user=Depends(get_current_user)
):
    db = SessionLocal()
    try:
        if not data.prompt or not data.prompt.strip():
            raise HTTPException(status_code=400, detail="Prompt is required")

        # Charge exactly ONCE per regen (premium feature behavior)
        _check_and_consume_once(db, user)

        section = data.section

        if section == "social":
            system = (
                "You are a world-class social copywriter.\n"
                "Output ONLY the posts. NO explanations.\n"
                "Write EXACTLY 5 posts. High-signal, non-generic.\n"
                "Strong hooks, clear value, natural CTA.\n"
            )
        elif section == "email":
            system = (
                "You write FINAL, SEND-READY business emails.\n"
                "NO explanations. Output ONLY:\n"
                "Subject: ...\n\n"
                "<body>\n"
                "Professional, confident, human. No hype.\n"
            )
        else:  # ads
            system = (
                "You generate HIGH-CONVERTING ads.\n"
                "Return ONLY ad content—no explanation.\n"
                "FORMAT STRICTLY:\n\n"
                "AD 1:\nHeadline:\nPrimary text:\nCTA:\n\n"
                "AD 2:\nHeadline:\nPrimary text:\nCTA:\n\n"
                "AD 3:\nHeadline:\nPrimary text:\nCTA:\n"
                "Make them specific and punchy.\n"
            )

        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": data.prompt},
            ]
        )

        out = (resp.choices[0].message.content or "").strip()
        if not out:
            raise HTTPException(500, "Empty AI response")

        # Save regen as its own item
        db.add(SavedContent(
            user_id=user.id,
            content_type=f"growth_pack_regen_{section}",
            prompt=data.prompt,
            result=out
        ))
        db.commit()

        image_url: Optional[str] = None

        if section == "ads" and data.generate_image:
            if not _is_paid(user):
                return {
                    "section": section,
                    "output": out,
                    "image": None,
                    "error": "AI Image is only available for paid users. Upgrade to unlock images."
                }

            visual_prompt = f"""
Create a high-quality, visually engaging marketing image.
NO TEXT IN THE IMAGE.
Modern, premium SaaS marketing look.

AD COPY (for inspiration):
{out[:900]}
"""

            img = client.images.generate(
                model="gpt-image-1",
                prompt=visual_prompt,
                size="1024x1024",
                response_format="url"
            )

            try:
                image_url = img.data[0].url
            except:
                try:
                    b64 = img.data[0].b64_json
                    image_url = f"data:image/png;base64,{b64}"
                except:
                    image_url = None

        return {
            "section": section,
            "output": out,
            "image": image_url,
            "error": None
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Regenerate error: {str(e)}")
    finally:
        db.close()
