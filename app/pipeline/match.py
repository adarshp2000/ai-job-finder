import re
from typing import Dict, Any

# Titles we NEVER want
EXCLUDE_TITLE_WORDS = [
    "intern", "internship",
    "contract", "temporary",
    "manager", "management",
    "director", "vp", "vice president",
    "head of",
    "principal",
    "lead", "tech lead",
    "staff", "senior staff",
]

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
        if re.search(rf"(?<!\w){re.escape(w)}(?!\w)", t):
            hits += 1
    return hits

def title_is_excluded(title: str) -> bool:
    t = norm(title)
    return any(x in t for x in EXCLUDE_TITLE_WORDS)

def is_excluded(job_text: str, prefs: Dict[str, Any]) -> bool:
    return contains_any(job_text, prefs.get("exclude", []))

def match_score(job: Dict[str, Any], prefs: Dict[str, Any]) -> tuple[bool, float, str]:
    """
    Returns: (is_match, score_0_to_1, reason)
    Rule-based scoring with title filtering + skill minimum.
    """
    title = job.get("title") or ""
    location = job.get("location") or ""
    desc = job.get("description") or ""
    text = f"{title}\n{location}\n{desc}"

    # HARD FILTERS
    if title_is_excluded(title):
        return (False, 0.0, "Excluded seniority/title")

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

    # NEW RULE: require at least 1 skill match if skills list is not empty
    if skills and skill_hits == 0:
        return (False, float(score), f"Rejected: no skill match. title_hit={title_hit:.0f}, loc_hit={loc_hit:.0f}")

    is_match = score >= 0.35
    reason = f"title_hit={title_hit:.0f}, skill_hits={skill_hits}, loc_hit={loc_hit:.0f}"
    return (is_match, float(score), reason)