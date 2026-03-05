import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, Tuple
import httpx

OUT_PATH = Path("sources.json")

# These are public curated lists that contain many career links.
# (You can add/remove seeds anytime.)
SEED_URLS = [
    # remote-jobs-resources (lots of boards.greenhouse.io links)
    "https://raw.githubusercontent.com/ineelhere/remote-jobs-resources/master/README.md",
    # awesome-easy-apply (companies using Lever/Greenhouse)
    "https://raw.githubusercontent.com/sample-resume/awesome-easy-apply/main/README.md",
    # easy-application (companies easy apply)
    "https://raw.githubusercontent.com/j-delaney/easy-application/master/README.md",
]

GH_RE = re.compile(r"https?://boards\.greenhouse\.io/([a-zA-Z0-9_-]+)")
LEVER_RE = re.compile(r"https?://jobs\.lever\.co/([a-zA-Z0-9_-]+)")

@dataclass(frozen=True)
class Source:
    type: str        # "greenhouse" | "lever"
    key: str         # token/handle
    company: Optional[str] = None

async def fetch_text(url: str) -> str:
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        r = await client.get(url)
        r.raise_for_status()
        return r.text

def extract_candidates(text: str) -> Tuple[set[str], set[str]]:
    gh = set(m.group(1).lower() for m in GH_RE.finditer(text))
    lever = set(m.group(1).lower() for m in LEVER_RE.finditer(text))
    return gh, lever

async def validate_greenhouse(tokens: Iterable[str]) -> set[str]:
    ok = set()
    async with httpx.AsyncClient(timeout=20) as client:
        for t in tokens:
            url = f"https://boards-api.greenhouse.io/v1/boards/{t}/jobs"
            try:
                r = await client.get(url)
                if r.status_code == 200:
                    ok.add(t)
            except Exception:
                pass
    return ok

async def validate_lever(handles: Iterable[str]) -> set[str]:
    ok = set()
    async with httpx.AsyncClient(timeout=20) as client:
        for h in handles:
            url = f"https://api.lever.co/v0/postings/{h}?mode=json"
            try:
                r = await client.get(url)
                if r.status_code == 200:
                    ok.add(h)
            except Exception:
                pass
    return ok

async def main():
    all_gh = set()
    all_lever = set()

    print("Downloading seed lists...")
    for u in SEED_URLS:
        try:
            txt = await fetch_text(u)
            gh, lv = extract_candidates(txt)
            print(f"- {u} -> greenhouse:{len(gh)} lever:{len(lv)}")
            all_gh |= gh
            all_lever |= lv
        except Exception as e:
            print(f"- {u} failed: {e}")

    print(f"\nFound candidates: greenhouse={len(all_gh)} lever={len(all_lever)}")
    print("Validating against public APIs (keeping only real boards)...")

    gh_ok = await validate_greenhouse(sorted(all_gh))
    lv_ok = await validate_lever(sorted(all_lever))

    sources: list[dict] = []
    for t in sorted(gh_ok):
        sources.append({"type": "greenhouse", "key": t, "company": t})
    for h in sorted(lv_ok):
        sources.append({"type": "lever", "key": h, "company": h})

    OUT_PATH.write_text(json.dumps(sources, indent=2), encoding="utf-8")
    print(f"\nWrote {len(sources)} sources to {OUT_PATH}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())