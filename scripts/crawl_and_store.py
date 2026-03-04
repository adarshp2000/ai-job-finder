import asyncio

from app.db.sqlite import init_db
from app.crawlers.lever import fetch_lever
from app.crawlers.greenhouse import fetch_greenhouse
from app.pipeline.store import upsert_job

LEVER_COMPANIES = []

# Add more greenhouse tokens later (these are examples; some may fail)
GREENHOUSE_TOKENS = [
    "airbnb",     # sometimes GH token matches company
    "datadog",
]

async def main():
    init_db()

    new_count = 0
    total = 0

    # Lever
    for c in LEVER_COMPANIES:
        try:
            jobs = await fetch_lever(c)
            print(f"Lever {c}: {len(jobs)} jobs")
            for j in jobs:
                is_new, _ = upsert_job(j)
                total += 1
                if is_new:
                    new_count += 1
        except Exception as e:
            print(f"Lever {c}: failed -> {e}")

    # Greenhouse
    for token in GREENHOUSE_TOKENS:
        try:
            jobs = await fetch_greenhouse(token)
            print(f"Greenhouse {token}: {len(jobs)} jobs")
            for j in jobs:
                is_new, _ = upsert_job(j)
                total += 1
                if is_new:
                    new_count += 1
        except Exception as e:
            print(f"Greenhouse {token}: failed -> {e}")

    print(f"\nDONE. Total processed: {total}, NEW inserted: {new_count}")
    print("Database at: data/jobs.db")

if __name__ == "__main__":
    asyncio.run(main())