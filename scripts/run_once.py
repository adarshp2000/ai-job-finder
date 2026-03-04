import asyncio
from app.crawlers.lever import fetch_lever

COMPANIES = ["netflix", "stripe", "airbnb"]

async def main():
    all_jobs = []
    for c in COMPANIES:
        try:
            jobs = await fetch_lever(c)
            print(f"{c}: {len(jobs)} jobs")
            all_jobs.extend(jobs)
        except Exception as e:
            print(f"{c}: failed -> {e}")

    print("\nTop 20 links:")
    for j in all_jobs[:20]:
        print(f"- {j['company']} | {j['title']} | {j.get('location')} | {j['url']}")

if __name__ == "__main__":
    asyncio.run(main())