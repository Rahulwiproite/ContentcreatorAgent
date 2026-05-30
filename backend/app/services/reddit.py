"""Reddit live trend fetcher via public RSS feeds (no auth, no rate-limit issues).

Reddit's JSON endpoints block bots aggressively, but the .rss endpoints stay open
for public reading. We parse RSS XML and extract title + score + URL.
"""
import re
from typing import Any, Dict, List
from xml.etree import ElementTree as ET

import httpx

BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)

ATOM = "{http://www.w3.org/2005/Atom}"

CATEGORY_SUBS: Dict[str, List[str]] = {
    "general": ["popular", "all", "india"],
    "comedy": ["funny", "memes", "IndianMemeTemplates", "Jokes", "ContagiousLaughter", "IndianDankMemes"],
    "fitness": ["Fitness", "bodyweightfitness", "naturalbodybuilding", "loseit"],
    "food": ["food", "IndianFood", "recipes", "MealPrepSunday", "cookingforbeginners"],
    "fashion": ["femalefashionadvice", "malefashionadvice", "streetwear", "TheGirlSurvivalGuide"],
    "beauty": ["MakeupAddiction", "SkincareAddiction", "Indian_Skincare_Addicts"],
    "tech": ["technology", "gadgets", "Android", "apple", "buildapc"],
    "gaming": ["gaming", "pcgaming", "IndianGaming"],
    "education": ["IndianStudents", "GetStudying", "JEENEETards", "UPSC"],
    "lifestyle": ["LifeProTips", "decidingtobebetter", "selfimprovement"],
    "business": ["Entrepreneur", "smallbusiness", "IndianStreetBets", "personalfinance"],
    "music": ["Music", "WeAreTheMusicMakers", "indianmusicians"],
    "travel": ["travel", "solotravel", "IndiaTravel"],
    "parenting": ["Parenting", "beyondthebump", "Mommit"],
    "relationships": ["relationship_advice", "dating_advice", "AskMen", "AskWomen"],
    "news": ["worldnews", "india", "unitedstatesofindia"],
    "motivation": ["GetMotivated", "decidingtobebetter"],
}


def categories() -> List[str]:
    return list(CATEGORY_SUBS.keys())


def _strip_html(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", s or "")
    return re.sub(r"\s+", " ", s).strip()


def _fetch_sub_rss(sub: str, limit: int = 10) -> List[Dict[str, Any]]:
    url = f"https://www.reddit.com/r/{sub}/hot.rss?limit={limit}"
    try:
        with httpx.Client(timeout=15, headers={"User-Agent": BROWSER_UA}) as c:
            res = c.get(url, follow_redirects=True)
            if res.status_code != 200:
                return []
            root = ET.fromstring(res.text)
    except Exception:
        return []

    out: List[Dict[str, Any]] = []
    for entry in root.findall(f"{ATOM}entry"):
        title_el = entry.find(f"{ATOM}title")
        link_el = entry.find(f"{ATOM}link")
        author_el = entry.find(f"{ATOM}author/{ATOM}name")
        title = _strip_html(title_el.text if title_el is not None else "")
        href = link_el.get("href") if link_el is not None else ""
        author = (author_el.text or "") if author_el is not None else ""
        if not title:
            continue
        out.append(
            {
                "subreddit": sub,
                "title": title[:240],
                "author": author,
                "url": href,
                "score": 0,
                "comments": 0,
            }
        )
    return out


def trends_for(category: str, per_sub: int = 8, max_posts: int = 30) -> Dict[str, Any]:
    cat = category if category in CATEGORY_SUBS else "general"
    subs = CATEGORY_SUBS[cat][:5]
    posts: List[Dict[str, Any]] = []
    for sub in subs:
        posts.extend(_fetch_sub_rss(sub, limit=per_sub))

    seen = set()
    deduped: List[Dict[str, Any]] = []
    for p in posts:
        key = p["title"][:80].lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(p)
        if len(deduped) >= max_posts:
            break

    return {
        "category": cat,
        "subs_scanned": subs,
        "top_posts": deduped,
        "count": len(deduped),
    }
