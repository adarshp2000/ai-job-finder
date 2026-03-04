import httpx

async def fetch_greenhouse(board_token: str) -> list[dict]:
    """
    Fetch list of jobs from Greenhouse board API.
    """
    url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs"
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(url)
        r.raise_for_status()
        data = r.json()

    jobs = []
    for j in data.get("jobs", []):
        jobs.append({
            "source": "greenhouse",
            "source_key": board_token,
            "external_id": str(j.get("id")),
            "title": j.get("title"),
            "company": None,  # you can map token->company later
            "location": (j.get("location") or {}).get("name"),
            "url": j.get("absolute_url"),
            # GH list endpoint has "updated_at" in some responses; keep best effort
            "posted_at": j.get("updated_at") or j.get("created_at"),
            "description": "",  # keep empty for now; later fetch detail page
        })
    return jobs