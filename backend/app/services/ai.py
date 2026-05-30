"""Provider-agnostic AI layer. Works for any creator category + any language."""
import json
from typing import Any, Dict, List, Optional

from ..config import get_settings
from . import gemini as gemini_provider
from .gemini import IDEAS_SCHEMA, ADVICE_SCHEMA


LANG_INSTRUCTIONS = {
    "hi": (
        "Output in HINDI - Devanagari script (देवनागरी). "
        "Hinglish phrases allowed inside Devanagari (e.g. 'WhatsApp ka status'), "
        "but the script must be Devanagari."
    ),
    "hinglish": (
        "Output in HINGLISH - Hindi written in Roman letters. "
        "Example: 'bhai yeh kya scene hai'. Mix English freely."
    ),
    "en": (
        "Output in clean conversational ENGLISH. "
        "Use slang appropriate to the platform."
    ),
}


CATEGORY_HINTS = {
    "comedy": "short-form comedy / sketch / observational humor",
    "fitness": "fitness, training, workout, gym, transformation, nutrition",
    "food": "food, recipes, cooking, restaurant reviews, street food",
    "fashion": "fashion, outfit ideas, styling, haul, trend breakdown",
    "beauty": "beauty, makeup, skincare, GRWM, product reviews",
    "tech": "tech, gadgets, apps, AI, productivity, coding",
    "gaming": "gaming, streaming, esports, game reviews, walkthroughs",
    "education": "education, study tips, exam prep, learning hacks, tutorials",
    "lifestyle": "lifestyle, daily routine, life hacks, self improvement",
    "business": "business, entrepreneurship, finance, startups, side hustle",
    "music": "music, covers, original tracks, music reviews",
    "travel": "travel, destinations, travel tips, vlogs",
    "parenting": "parenting, kids, family life, parenting hacks",
    "relationships": "dating, relationships, marriage, friendship",
    "news": "news commentary, current events, analysis",
    "motivation": "motivation, mindset, self-help, productivity",
    "general": "general lifestyle / pop culture content",
}


def _lang_instr(lang: str) -> str:
    return LANG_INSTRUCTIONS.get((lang or "en").lower(), LANG_INSTRUCTIONS["en"])


def _cat_hint(category: str) -> str:
    return CATEGORY_HINTS.get((category or "general").lower(), CATEGORY_HINTS["general"])


def _ideation_system(category: str, language: str) -> str:
    return f"""You are a world-class short-form video strategist who has helped {category} creators
go viral on Instagram Reels, TikTok and YouTube Shorts. You understand:
- 3-second hook discipline
- platform-native formats and current meme grammar
- pattern interrupts, surprise, exaggeration, authenticity
- how to translate a live trend into THIS creator's niche

Category focus: {_cat_hint(category)}

{_lang_instr(language)}

You ONLY respond with valid JSON matching the requested schema. No prose, no markdown."""


def _ideation_prompt(
    count: int, niche: str, vibe: str, length: str, platform: str,
    trends_json: str, top_posts_json: str
) -> str:
    return f"""Generate {count} fresh, original short-form video ideas.

Creator's specific niche: {niche}
Vibe: {vibe}
Target length: {length}
Target platform: {platform}

LIVE TRENDING content scraped right now from Reddit + X (use these as fuel, do NOT copy them verbatim;
extract the underlying pattern/format/topic and translate to creator's niche):
{trends_json}

Creator's recent top-performing posts (if any; mimic the rhythm of what works for them):
{top_posts_json}

Return JSON with shape:
{{
  "ideas": [
    {{
      "title": "short punchy name",
      "hook": "first 3 seconds - spoken or text-on-screen",
      "script_outline": "3-6 short beats, each on a new line starting with '- '",
      "hashtags": ["#tag1", "#tag2", "..."],
      "suggested_time": "e.g. Tue 7:00 PM IST",
      "virality_score": 0.0
    }}
  ]
}}

virality_score is your honest 0-1 estimate for THIS creator. Be picky."""


def _script_system(category: str, language: str) -> str:
    return f"""You are a viral short-form video script writer for {category} creators.
You take one idea and produce a complete, shootable 30-second reel script.

Format requirements:
- Use [TIMESTAMP] and [DIRECTION] markers
- "SPOKEN:" prefix for dialogue (with character/speaker name)
- "TEXT ON SCREEN:" prefix for on-screen captions
- End with a punchy line / call-to-action that earns replay or share

{_lang_instr(language)}

Return plain text - NO JSON, NO markdown code blocks."""


def _script_prompt(niche: str, title: str, hook: str, outline: str) -> str:
    return f"""Niche: {niche}
Idea title: {title}
Hook: {hook}
Outline:
{outline}

Write the full shootable 30-second reel script now. Include timestamps,
directions, dialogue and on-screen text."""


def _advice_system(language: str) -> str:
    return f"""You are a brutally honest short-form video analyst. You spot why posts under-perform
and prescribe specific, testable fixes.

{_lang_instr(language)}

Respond ONLY in valid JSON matching the requested schema."""


def _advice_prompt(niche: str, posts_json: str) -> str:
    return f"""Creator niche: {niche}

Recent posts (newest first):
{posts_json}

Return JSON:
{{
  "summary": "2-3 sentence honest diagnosis",
  "best_times": ["Day HH:MM", "..."],
  "actions": [
    {{"title":"...", "why":"...", "do_this":"..."}}
  ]
}}
"""


def _provider() -> str:
    s = get_settings()
    if s.AI_PROVIDER:
        return s.AI_PROVIDER.lower()
    if s.GEMINI_API_KEY:
        return "gemini"
    if s.ANTHROPIC_API_KEY:
        return "claude"
    raise RuntimeError(
        "No AI provider configured. Set GEMINI_API_KEY (free) or ANTHROPIC_API_KEY in .env"
    )


def _call(system: str, prompt: str, fast: bool = False, json_mode: bool = True, schema=None) -> str:
    s = get_settings()
    provider = _provider()
    if provider == "gemini":
        model = s.GEMINI_MODEL_FAST if fast else s.GEMINI_MODEL_IDEATION
        return gemini_provider.generate(system, prompt, model=model, json_mode=json_mode, schema=schema)
    if provider == "claude":
        import anthropic
        client = anthropic.Anthropic(api_key=s.ANTHROPIC_API_KEY)
        model = s.CLAUDE_MODEL_FAST if fast else s.CLAUDE_MODEL_IDEATION
        msg = client.messages.create(
            model=model,
            max_tokens=2500,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
    raise RuntimeError(f"Unknown AI_PROVIDER: {provider}")


def _extract_json(text: str) -> Dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        return {}
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return {}


def generate_ideas(
    niche: str,
    category: str,
    language: str,
    vibe: str,
    length: str,
    platform: str,
    count: int,
    trends: Dict[str, Any],
    top_posts: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    sys = _ideation_system(category, language)
    prompt = _ideation_prompt(
        count=count, niche=niche or category, vibe=vibe, length=length, platform=platform,
        trends_json=json.dumps(trends, ensure_ascii=False)[:7000],
        top_posts_json=json.dumps(top_posts, ensure_ascii=False)[:4000],
    )
    text = _call(sys, prompt, fast=False, json_mode=True, schema=IDEAS_SCHEMA)
    return _extract_json(text).get("ideas", [])


def generate_full_script(
    niche: str, category: str, language: str,
    title: str, hook: str, outline: str
) -> str:
    sys = _script_system(category, language)
    prompt = _script_prompt(niche or category, title, hook, outline)
    text = _call(sys, prompt, fast=False, json_mode=False)
    return text.strip()


def engagement_advice(
    niche: str, language: str, recent_posts: List[Dict[str, Any]]
) -> Dict[str, Any]:
    sys = _advice_system(language)
    prompt = _advice_prompt(niche, json.dumps(recent_posts, ensure_ascii=False)[:7000])
    text = _call(sys, prompt, fast=True, json_mode=True, schema=ADVICE_SCHEMA)
    return _extract_json(text)


def current_provider() -> str:
    try:
        return _provider()
    except RuntimeError:
        return "none"


def list_categories() -> List[str]:
    return list(CATEGORY_HINTS.keys())


def list_languages() -> List[Dict[str, str]]:
    return [
        {"code": "en", "label": "English"},
        {"code": "hi", "label": "Hindi (Devanagari)"},
        {"code": "hinglish", "label": "Hinglish (Roman)"},
    ]
