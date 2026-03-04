import re
from typing import Dict, Any

def norm(s: str) -> str:
    return (s or "").lower()

def contains_any(text: str, words: list[str]) -> bool:
    t = norm(text)
    return any(w.lower() in t for w in words if w and w.strip())

def word_hits(text: str, words: list[str]) -> int:
    t = norm(text)
    hits = 0
    for w in words:
        w = w.strip().lower()
        if not w:
            continue
        # simple boundary-ish match
        if re.search(rf"(?<!\w){re.escape(w)}(?!\w)", t):
            hits += 1
    return hits

def is_excluded(job_text: str, prefs: Dict[str, Any]) -> bool:
    return contains_any(job_text, prefs.get("exclude", []))

def match_score(job: Dict[str, Any], prefs: Dict[str, Any]) -> tuple[bool, float, str]:
    """
    Returns: (is_match, score_0_to_1, reason)
    Simple rule-based scoring.
    """
    title = job.get("title") or ""
    location = job.get("location") or ""
    desc = job.get("description") or ""
    text = f"{title}\n{location}\n{desc}"

    if is_excluded(text, prefs):
        return (False, 0.0, "Excluded keyword")

    # title relevance
    title_hit = 1.0 if contains_any(title, prefs.get("titles", [])) else 0.0

    # skill hits
    skills = prefs.get("skills", [])
    skill_hits = word_hits(text, skills)
    skill_score = min(skill_hits / max(len(skills), 1), 1.0)

    # location match (soft)
    loc_hit = 1.0 if contains_any(location, prefs.get("locations", [])) else 0.0

    # combine
    score = 0.55 * title_hit + 0.35 * skill_score + 0.10 * loc_hit

    is_match = score >= 0.35  # threshold; tune this
    reason = f"title_hit={title_hit:.0f}, skill_hits={skill_hits}, loc_hit={loc_hit:.0f}"

    return (is_match, float(score), reason)