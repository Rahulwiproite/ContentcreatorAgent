import json
from typing import Any, Dict, List, Optional

import anthropic

from ..config import get_settings

settings = get_settings()


def _client() -> anthropic.Anthropic:
    if not settings.ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY not configured")
    return anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)


IDEATION_SYSTEM = """You are a world-class short-form video comedy strategist who has helped creators
go viral on Instagram Reels, TikTok and YouTube Shorts. You understand:
- 3-second hook discipline
- pattern interrupts, surprise, status-play, exaggeration, observational comedy
- platform-native formats and current meme grammar
- when a creator's niche overlaps with a trend

You ONLY respond with valid JSON matching the requested schema. No prose."""


IDEATION_USER_TEMPLATE = """Generate {count} fresh, original short-form video ideas for a comedy creator.

Creator niche: {niche}
Desired vibe: {vibe}
Target length: {length}
Target platform: {platform}

Current trends across platforms (use these as fuel, do not copy them):
{trends_json}

Creator's recent top-performing posts (mimic the rhythm of what works for them):
{top_posts_json}

Return JSON with this exact shape:
{{
  "ideas": [
    {{
      "title": "short punchy name",
      "hook": "first 3 seconds, spoken or text-on-screen",
      "script_outline": "3-6 short bullet beats separated by \\n- ",
      "hashtags": ["#tag1", "#tag2", "..."],
      "suggested_time": "e.g. Tue 7:00 PM IST",
      "virality_score": 0.0
    }}
  ]
}}

virality_score is your honest 0-1 estimate for THIS creator. Be picky."""


def generate_ideas(
    niche: str,
    vibe: str,
    length: str,
    platform: str,
    count: int,
    trends: Dict[str, Any],
    top_posts: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    client = _client()
    msg = client.messages.create(
        model=settings.CLAUDE_MODEL_IDEATION,
        max_tokens=2500,
        system=IDEATION_SYSTEM,
        messages=[
            {
                "role": "user",
                "content": IDEATION_USER_TEMPLATE.format(
                    count=count,
                    niche=niche or "general comedy",
                    vibe=vibe,
                    length=length,
                    platform=platform,
                    trends_json=json.dumps(trends, ensure_ascii=False)[:8000],
                    top_posts_json=json.dumps(top_posts, ensure_ascii=False)[:8000],
                ),
            }
        ],
    )
    text = "".join(block.text for block in msg.content if getattr(block, "type", "") == "text")
    data = _extract_json(text)
    return data.get("ideas", [])


ADVICE_SYSTEM = """You are a brutally honest short-form video analyst. You spot exactly why
a creator's posts under-perform and prescribe specific, testable fixes.
Respond ONLY in valid JSON."""


def engagement_advice(niche: str, recent_posts: List[Dict[str, Any]]) -> Dict[str, Any]:
    client = _client()
    msg = client.messages.create(
        model=settings.CLAUDE_MODEL_FAST,
        max_tokens=1500,
        system=ADVICE_SYSTEM,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Creator niche: {niche}\n\n"
                    f"Recent posts (sorted newest first) with metrics:\n"
                    f"{json.dumps(recent_posts, ensure_ascii=False)[:9000]}\n\n"
                    "Return JSON:\n"
                    "{\n"
                    '  "summary": "2-3 sentence honest diagnosis",\n'
                    '  "best_times": ["Day HH:MM", "..."],\n'
                    '  "actions": [\n'
                    '    {"title":"...", "why":"...", "do_this":"..."}\n'
                    "  ]\n"
                    "}\n"
                ),
            }
        ],
    )
    text = "".join(block.text for block in msg.content if getattr(block, "type", "") == "text")
    return _extract_json(text)


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
