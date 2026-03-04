import asyncio
import json
from pathlib import Path

from app.db.sqlite import init_db
from app.crawlers.lever import fetch_lever
from app.crawlers.greenhouse import fetch_greenhouse
from app.pipeline.store import upsert_job

SOURCES_PATH = Path("sources.json")

def load_sources():
    if not SOURCES_PATH.exists():
        print("sources.json not found in project root.")
        return []
    return json.loads(SOURCES_PATH.read_text(encoding="utf-8"))

async def main():
    init_db()

    new_count = 0
    total = 0

    sources = load_sources()
    print(f"Loaded sources: {len(sources)}")

    # Don’t melt your laptop: crawl in batches
    MAX_SOURCES_PER_RUN = 40  # increase later (ex: 100)
    sources = sources[:MAX_SOURCES_PER_RUN]

    for s in sources:
        source_type = s.get("type")
        key = s.get("key")
        company = s.get("company") or key

        try:
            if source_type == "greenhouse":
                jobs = await fetch_greenhouse(key)
                print(f"Greenhouse {key}: {len(jobs)} jobs")
                for j in jobs:
                    j["company"] = company
                    is_new, _ = upsert_job(j)
                    total += 1
                    if is_new:
                        new_count += 1

            elif source_type == "lever":
                jobs = await fetch_lever(key)
                print(f"Lever {key}: {len(jobs)} jobs")
                for j in jobs:
                    j["company"] = company
                    is_new, _ = upsert_job(j)
                    total += 1
                    if is_new:
                        new_count += 1

        except Exception as e:
            print(f"{source_type} {key}: failed -> {e}")

    print(f"\nDONE. Total processed: {total}, NEW inserted: {new_count}")
    print("Database at: data/jobs.db")

if __name__ == "__main__":
    asyncio.run(main())