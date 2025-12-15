def build_profile_context(profile):
    """
    Creates a structured block of user profile information that can be injected
    into every AI prompt. Medium personalization: helpful but not overpowering.
    """

    if profile is None:
        return "User has no saved profile information."

    return f"""
USER PROFILE CONTEXT:
---------------------
Full Name: {profile.full_name or "N/A"}
Title: {profile.title or "N/A"}
Company Name: {profile.company_name or "N/A"}
Company Website: {profile.company_website or "N/A"}

Brand Tone: {profile.brand_tone or "N/A"}
Industry: {profile.industry or "N/A"}
Brand Description: {profile.brand_description or "N/A"}
Target Audience: {profile.target_audience or "N/A"}

Preferred Writing Style: {profile.writing_style or "N/A"}
Email Signature (use when writing emails): {profile.signature or "N/A"}

Instructions to AI:
- Use these details to personalize content naturally.
- Do not force or exaggerate usage.
- If information is missing, generate neutral content.
- Keep outputs clean, helpful and professional.
---------------------
"""
