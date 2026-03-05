import httpx
from app.utils.text import html_to_text

# Public GH board endpoint gives listings
LIST_URL = "https://boards-api.greenhouse.io/v1/boards/{token}/jobs"
DETAIL_URL = "https://boards-api.greenhouse.io/v1/boards/{token}/jobs/{job_id}"

async def fetch_greenhouse(token: str) -> list[dict]:
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        r = await client.get(LIST_URL.format(token=token))
        r.raise_for_status()
        data = r.json()

        jobs = []
        for j in data.get("jobs", []):
            job_id = j.get("id")
            title = j.get("title")
            location = (j.get("location") or {}).get("name")
            url = j.get("absolute_url")
            updated_at = j.get("updated_at")

            description = ""
            # --- hydrate description from job detail endpoint ---
            try:
                dr = await client.get(DETAIL_URL.format(token=token, job_id=job_id))
                if dr.status_code == 200:
                    d = dr.json()
                    # ✅ Convert GH HTML content to clean text
                    description = html_to_text(d.get("content") or "")
            except Exception:
                description = ""

            jobs.append(
                {
                    "source": "greenhouse",
                    "source_key": token,
                    "source_id": str(job_id),
                    "title": title,
                    "company": token,
                    "location": location,
                    "url": url,
                    "posted_at": updated_at,
                    "description": description,  # ✅ now plain text
                }
            )

        return jobs