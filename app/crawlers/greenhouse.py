import asyncio
import httpx

LIST_URL = "https://boards-api.greenhouse.io/v1/boards/{token}/jobs"
DETAIL_URL = "https://boards-api.greenhouse.io/v1/boards/{token}/jobs/{job_id}"


async def fetch_greenhouse(
    token: str,
    hydrate: bool = True,
    detail_concurrency: int = 15,  # keep 10–20 on a laptop
) -> list[dict]:
    timeout = httpx.Timeout(30.0)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        r = await client.get(LIST_URL.format(token=token))
        r.raise_for_status()
        data = r.json()

        jobs_raw = data.get("jobs", [])

        # If you DON'T want full descriptions:
        if not hydrate:
            return [
                {
                    "source": "greenhouse",
                    "source_key": token,
                    "source_id": str(j.get("id")),
                    "title": j.get("title"),
                    "company": token,
                    "location": (j.get("location") or {}).get("name"),
                    "url": j.get("absolute_url"),
                    "posted_at": j.get("updated_at"),
                    "description": "",
                }
                for j in jobs_raw
            ]

        sem = asyncio.Semaphore(detail_concurrency)

        async def fetch_detail(job_id: int) -> str:
            async with sem:
                try:
                    dr = await client.get(DETAIL_URL.format(token=token, job_id=job_id))
                    if dr.status_code == 200:
                        d = dr.json()
                        return d.get("content") or ""
                except Exception:
                    pass
                return ""

        # fire detail requests in parallel (limited by semaphore)
        detail_tasks = [fetch_detail(j.get("id")) for j in jobs_raw]
        descriptions = await asyncio.gather(*detail_tasks)

        jobs = []
        for j, description in zip(jobs_raw, descriptions):
            job_id = j.get("id")
            jobs.append(
                {
                    "source": "greenhouse",
                    "source_key": token,
                    "source_id": str(job_id),
                    "title": j.get("title"),
                    "company": token,
                    "location": (j.get("location") or {}).get("name"),
                    "url": j.get("absolute_url"),
                    "posted_at": j.get("updated_at"),
                    "description": description,  # ✅ filled
                }
            )

        return jobs