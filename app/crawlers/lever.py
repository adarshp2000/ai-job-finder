import httpx

async def fetch_lever(company: str) -> list[dict]:
    url = f"https://api.lever.co/v0/postings/{company}?mode=json"
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(url)
        r.raise_for_status()
        data = r.json()

    jobs = []
    for j in data:
        # Lever nests location inside "categories" — this is the correct key
        categories = j.get("categories") or {}
        location = (
            categories.get("location")        # e.g. "New York, NY"
            or categories.get("commitment")   # fallback: "Full-time"
            or j.get("workplaceType")         # fallback: "remote"
            or ""
        )

        # Grab plain-text description (Lever provides both HTML and plain)
        description = (
            j.get("descriptionPlain")
            or j.get("description")
            or ""
        )

        jobs.append({
            "source": "lever",
            "source_key": company,
            "company": company,
            "title": j.get("text"),
            "location": location,
            "url": j.get("hostedUrl"),
            "description": description,
        })

    return jobs