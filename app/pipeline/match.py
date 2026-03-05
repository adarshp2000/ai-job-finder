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
    "staff", "senior",
]

# 2-letter US states (for patterns like "Austin, TX" / "Remote, US" / "NY")
US_STATES = {
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN","IA","KS","KY","LA","ME","MD",
    "MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ","NM","NY","NC","ND","OH","OK","OR","PA","RI","SC",
    "SD","TN","TX","UT","VT","VA","WA","WV","WI","WY","DC"
}

# Words that strongly imply NOT US — expanded significantly
NON_US_HINTS = [
    # Countries
    "canada", "india", "uk", "united kingdom", "australia", "israel",
    "netherlands", "sweden", "denmark", "italy", "germany", "france",
    "spain", "portugal", "switzerland", "austria", "belgium",
    "norway", "finland", "poland", "romania", "ukraine",
    "pakistan", "philippines", "vietnam", "indonesia", "malaysia",
    "nigeria", "kenya", "south africa", "new zealand",
    "japan", "china", "south korea", "taiwan", "hong kong",
    "mexico", "brazil", "argentina", "colombia",
    "singapore", "bahrain", "dubai", "abu dhabi",
    "hungary", "israel",
    # Cities
    "amsterdam", "london", "dublin", "paris", "berlin", "munich",
    "budapest", "shenzhen", "bengaluru", "bangalore", "chennai",
    "toronto", "ontario", "montreal", "vancouver",
    "sydney", "melbourne", "tel aviv",
    "madrid", "lisbon", "zurich", "brussels", "oslo", "helsinki",
    "warsaw", "bucharest", "kyiv",
    "tokyo", "beijing", "shanghai", "seoul", "taipei",
    "sao paulo", "mexico city", "bogota",
    # Regions
    "emea", "europe", "apac", "latam", "mena",
    "global", "worldwide", "international",
]

def norm(s: str) -> str:
    return (s or "").lower().strip()

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

    # normalize separators so "Senior/Staff" becomes "senior staff"
    t = re.sub(r"[^a-z0-9]+", " ", t)

    # word boundary-ish match (works for: "Senior", "Senior/Staff", "Senior-Staff", etc.)
    for w in EXCLUDE_TITLE_WORDS:
        w = norm(w).strip()
        if not w:
            continue
        if re.search(rf"(^|\s){re.escape(w)}(\s|$)", t):
            return True

    return False

def is_excluded(job_text: str, prefs: Dict[str, Any]) -> bool:
    return contains_any(job_text, prefs.get("exclude", []))

def is_us_only_location(location: str) -> bool:
    loc = norm(location)

    # No location = reject (can't confirm it's US)
    if not loc:
        return False

    # Reject if any non-US hint appears
    if any(x in loc for x in NON_US_HINTS):
        return False

    # Accept explicit US mentions
    if re.search(r"\b(united states|united states of america|u\.s\.a\.|usa|u\.s\.)\b", loc):
        return True

    # Accept "Remote (US)" / "Remote, US" / "US Remote"
    if re.search(r"\bremote\b.*\b(us|u\.s\.)\b", loc) or re.search(r"\b(us|u\.s\.)\b.*\bremote\b", loc):
        return True

    # Accept common "City, ST" pattern for US states e.g. "Austin, TX"
    m = re.search(r",\s*([A-Z]{2})\b", location)  # use original to preserve caps
    if m and m.group(1) in US_STATES:
        return True

    # Accept bare state abbreviation e.g. "NY", "CA"
    if re.search(r"\b(" + "|".join(US_STATES) + r")\b", location):
        return True

    # Bare "Remote" with no country context = reject (too ambiguous)
    if re.search(r"^\s*remote\s*$", loc):
        return False

    # Everything else = reject (unknown location)
    return False

def match_score(job: Dict[str, Any], prefs: Dict[str, Any]) -> tuple[bool, float, str]:
    """
    Returns: (is_match, score_0_to_1, reason)
    """
    title = job.get("title") or ""
    location = job.get("location") or ""
    desc = job.get("description") or ""
    text = f"{title}\n{location}\n{desc}"

    # HARD FILTERS (run FIRST)
    if not is_us_only_location(location):
        return (False, 0.0, "Rejected: Non-US location")

    if title_is_excluded(title):
        return (False, 0.0, "Rejected: Excluded seniority/title")

    if is_excluded(text, prefs):
        return (False, 0.0, "Rejected: Excluded keyword")

    # title relevance
    title_hit = 1.0 if contains_any(title, prefs.get("titles", [])) else 0.0

    # skill hits
    skills = prefs.get("skills", [])
    skill_hits = word_hits(text, skills)
    skill_score = min(skill_hits / max(len(skills), 1), 1.0)

    # location match (soft) - optional scoring bump
    loc_hit = 1.0 if contains_any(location, prefs.get("locations", [])) else 0.0

    # combine
    score = 0.55 * title_hit + 0.35 * skill_score + 0.10 * loc_hit

    # require at least 1 skill match if skills list is not empty
    if skills and skill_hits == 0:
        return (False, float(score), f"Rejected: no skill match. title_hit={title_hit:.0f}, loc_hit={loc_hit:.0f}")

    is_match = score >= 0.50
    reason = f"title_hit={title_hit:.0f}, skill_hits={skill_hits}, loc_hit={loc_hit:.0f}"
    return (is_match, float(score), reason)