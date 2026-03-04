import httpx

async def fetch_lever(company: str) -> list[dict]:
    url = f"https://api.lever.co/v0/postings/{company}?mode=json"
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(url)
        r.raise_for_status()
        data = r.json()

    jobs = []
    for j in data:
        jobs.append({
            "company": company,
            "title": j.get("text"),
            "location": (j.get("categories") or {}).get("location"),
            "url": j.get("hostedUrl"),
        })
    return jobs