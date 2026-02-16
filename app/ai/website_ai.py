import random
import hashlib
import json
from typing import Dict, Any, List, Tuple
from app.ai.openai_client import chat_completion

# --- DESIGN SYSTEM CONFIG ---
# We use these constants to keep the "Glass" look consistent across all variants
GLASS_BASE = "backdrop-blur-xl bg-white/5 border border-white/10 shadow-2xl"
ANIMATION_SLOW = "transition-all duration-1000 ease-in-out"

# --- THEMES (Expanded for variety) ---
COLOR_PALETTES = {
    "cyber_punk": {"primary": "from-fuchsia-600 to-purple-700", "accent": "fuchsia-400", "bg": "bg-slate-950", "text": "text-white", "blob": "bg-fuchsia-500/20"},
    "oceanic": {"primary": "from-blue-600 to-cyan-500", "accent": "cyan-400", "bg": "bg-gray-950", "text": "text-white", "blob": "bg-blue-500/20"},
    "minimal_dark": {"primary": "from-zinc-700 to-black", "accent": "zinc-400", "bg": "bg-neutral-950", "text": "text-zinc-100", "blob": "bg-white/5"},
    "forest_glow": {"primary": "from-emerald-600 to-teal-800", "accent": "emerald-400", "bg": "bg-stone-950", "text": "text-stone-50", "blob": "bg-emerald-500/10"}
}

# --- THE COMPONENT LIBRARY ---
# These are the "Blueprints". The AI will pick which 'variant' to use.
LAYOUT_VARIANTS = {
    "hero": {
        "split": """
            <section class="relative min-h-screen flex items-center {bg} pt-20">
                <div class="absolute inset-0 overflow-hidden"><div class="absolute -top-24 -right-24 w-96 h-96 {blob} blur-[120px] rounded-full"></div></div>
                <div class="container mx-auto px-6 grid lg:grid-cols-2 gap-16 items-center relative z-10">
                    <div class="reveal-text">
                        <span class="inline-block px-4 py-1 rounded-full border border-{accent}/30 text-{accent} text-sm mb-6 uppercase tracking-widest">{tagline}</span>
                        <h1 class="text-7xl lg:text-8xl font-black {text} leading-[0.9] mb-8">{headline}</h1>
                        <p class="text-xl text-gray-400 mb-12 max-w-lg leading-relaxed">{subheadline}</p>
                        <div class="flex flex-wrap gap-5">
                            <button class="px-10 py-5 bg-gradient-to-r {primary} text-white rounded-2xl font-bold shadow-xl hover:scale-105 {animation}">{cta_main}</button>
                            <button class="px-10 py-5 border border-white/10 {glass} rounded-2xl text-white font-bold hover:bg-white/5">{cta_sub}</button>
                        </div>
                    </div>
                    <div class="relative group">
                        <div class="absolute -inset-1 bg-gradient-to-r {primary} rounded-[2.5rem] blur opacity-25 group-hover:opacity-50 {animation}"></div>
                        <img src="{image_url}" class="relative rounded-[2rem] border border-white/10 object-cover w-full h-[600px] shadow-2xl" alt="Hero">
                    </div>
                </div>
            </section>""",
        "centered": """
            <section class="relative min-h-screen flex items-center justify-center text-center {bg} overflow-hidden">
                <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full h-full {blob} blur-[180px] opacity-30"></div>
                <div class="container mx-auto px-6 relative z-10">
                    <h1 class="text-8xl lg:text-[10rem] font-black {text} tracking-tighter leading-none mb-10">{headline}</h1>
                    <p class="text-2xl text-gray-400 max-w-3xl mx-auto mb-16">{subheadline}</p>
                    <button class="px-12 py-6 bg-white text-black rounded-full font-black text-xl hover:scale-110 {animation}">{cta_main}</button>
                </div>
            </section>"""
    },
    "features": {
        "grid": """
            <section class="py-32 {bg} relative">
                <div class="container mx-auto px-6">
                    <div class="mb-20 text-center">
                        <h2 class="text-5xl font-bold {text} mb-4">{title}</h2>
                        <p class="text-gray-500 max-w-2xl mx-auto">{subtitle}</p>
                    </div>
                    <div class="grid md:grid-cols-3 gap-8">
                        {feature_items}
                    </div>
                </div>
            </section>"""
    }
}

def _generate_feature_item(item_data, palette, glass):
    return f"""
    <div class="{glass} p-10 rounded-[2.5rem] group hover:-translate-y-3 transition-all duration-500">
        <div class="w-16 h-16 bg-gradient-to-br {palette['primary']} rounded-2xl flex items-center justify-center mb-8 group-hover:rotate-12 transition-transform">
            <span class="text-2xl">✨</span>
        </div>
        <h3 class="text-2xl font-bold text-white mb-4">{item_data['title']}</h3>
        <p class="text-gray-400 leading-relaxed">{item_data['desc']}</p>
    </div>"""

def generate_ai_sections(business_name: str, prompt: str):
    # 1. First, ask AI to be the "Architect"
    # We ask for JSON because it's much more reliable than raw HTML generation
    architect_prompt = f"""
    Generate a modern website architecture for "{business_name}".
    Description: {prompt}
    
    You must decide:
    1. Which Hero Variant to use: 'split' (for tech/agency) or 'centered' (for luxury/modern).
    2. Write high-conversion copy. No generic "Welcome" text.
    3. Generate 3 specific features based on the business description.
    4. Provide Unsplash keywords for images (e.g. "minimalist architecture dark").
    
    Return ONLY this JSON:
    {{
      "hero_variant": "split|centered",
      "copy": {{
        "tagline": "...", "headline": "...", "subheadline": "...", "cta_main": "...", "cta_sub": "...", "image_keywords": "..."
      }},
      "features": {{
        "title": "...", "subtitle": "...",
        "items": [
          {{"title": "Feature 1", "desc": "..."}},
          {{"title": "Feature 2", "desc": "..."}},
          {{"title": "Feature 3", "desc": "..."}}
        ]
      }}
    }}
    """
    
    try:
        response = chat_completion(
            system="You are a JSON-only API. No conversation.",
            user=architect_prompt,
            temperature=0.8
        )
        data = json.loads(response.strip().replace("```json", "").replace("```", ""))
        
        # 2. Pick a random palette to ensure variety
        p_key = random.choice(list(COLOR_PALETTES.keys()))
        p = COLOR_PALETTES[p_key]
        
        # 3. Build the HTML from the data (Hydration)
        final_html = {}
        
        # Build Hero
        variant = data.get("hero_variant", "split")
        img_url = f"https://images.unsplash.com/photo-1?auto=format&fit=crop&q=80&w=1200&keywords={data['copy'].get('image_keywords')}"
        
        hero_html = LAYOUT_VARIANTS["hero"][variant].format(
            **p, **data['copy'], glass=GLASS_BASE, animation=ANIMATION_SLOW, image_url=img_url
        )
        final_html["hero"] = hero_html
        
        # Build Features
        f_data = data["features"]
        items_html = "".join([_generate_feature_item(i, p, GLASS_BASE) for i in f_data["items"]])
        
        features_html = LAYOUT_VARIANTS["features"]["grid"].format(
            **p, title=f_data["title"], subtitle=f_data["subtitle"], feature_items=items_html
        )
        final_html["features"] = features_html
        
        return {
            "html": final_html,
            "palette": p_key,
            "business_name": business_name
        }

    except Exception as e:
        print(f"Build Failed: {e}")
        return {"error": str(e)}

# --- MAIN ENTRY ---
def generate_ai_plan(ai_input: Dict[str, Any]) -> Dict[str, Any]:
    prompt = ai_input.get("prompt", "")
    name = ai_input.get("business_name", "Brand")
    
    # This structure is what your frontend will receive
    result = generate_ai_sections(name, prompt)
    
    return {
        "content": result
    }