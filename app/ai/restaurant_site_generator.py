from typing import Dict
import json
from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_restaurant_website(data: Dict) -> Dict:
    """
    data = {
        "name": str,
        "cuisine": str,
        "city": str,
        "phone": str,
        "email": str (optional)
    }
    """

    prompt = f"""
You are generating JSON for a REAL restaurant website.

STRICT RULES:
- Output ONLY valid JSON
- NO markdown
- NO comments
- NO explanations

Restaurant info:
Name: {data['name']}
Cuisine: {data['cuisine']}
City: {data['city']}

JSON STRUCTURE (must match exactly):

{{
  "hero": {{
    "headline": "...",
    "subheadline": "..."
  }},
  "promo": {{
    "text": "..."
  }},
  "about": {{
    "text": "..."
  }},
  "hours": {{
    "monday": "...",
    "tuesday": "...",
    "wednesday": "...",
    "thursday": "...",
    "friday": "...",
    "saturday": "...",
    "sunday": "..."
  }},
  "contact": {{
    "phone": "{data['phone']}",
    "email": "{data.get('email', '')}",
    "address": "{data['city']}"
  }}
}}

Make it professional, realistic, and suitable for a restaurant homepage.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You generate clean website JSON. You never explain anything."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.6,
    )

    raw = response.choices[0].message.content.strip()

    return json.loads(raw)
