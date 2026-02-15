import re
from difflib import SequenceMatcher


def score_candidate(query: str, item: dict) -> float:
    title = (item.get("title") or "").lower()
    channel = (item.get("channel") or item.get("uploader") or "").lower()
    query_l = query.lower()

    score = 0.0
    score += SequenceMatcher(None, query_l, title).ratio() * 0.55
    score += SequenceMatcher(None, query_l, channel).ratio() * 0.15
    if "official" in title or "official" in channel:
        score += 0.1
    if "topic" in channel:
        score += 0.08
    if re.search(r"\b(live|cover|remix)\b", title):
        score -= 0.15
    views = float(item.get("view_count") or 0)
    if views > 0:
        score += min(0.25, (views / 50_000_000.0))
    return max(0.0, min(1.0, score))
