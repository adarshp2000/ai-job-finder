import asyncio
import json
from pathlib import Path

from app.db.sqlite import init_db
from app.crawlers.lever import fetch_lever
from app.crawlers.greenhouse import fetch_greenhouse
from app.pipeline.store import upsert_job

SOURCES_PATH = Path("sources.json")
STATE_PATH = Path("data/crawl_state.json")

MAX_SOURCES_PER_RUN = 40      # batch size (rotation)
CONCURRENCY = 10              # safe laptop default: 8–15


def load_sources():
    if not SOURCES_PATH.exists():
        print("sources.json not found in project root.")
        return []
    return json.loads(SOURCES_PATH.read_text(encoding="utf-8"))


def load_state():
    if not STATE_PATH.exists():
        return {"offset": 0}

    txt = STATE_PATH.read_text(encoding="utf-8").strip()
    if not txt:
        return {"offset": 0}

    try:
        return json.loads(txt)
    except json.JSONDecodeError:
        return {"offset": 0}


def save_state(state: dict):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")


def select_rotating_batch(sources: list[dict]) -> tuple[list[dict], int]:
    state = load_state()
    offset = int(state.get("offset", 0))

    batch = sources[offset: offset + MAX_SOURCES_PER_RUN]

    # wrap around
    if not batch:
        offset = 0
        batch = sources[:MAX_SOURCES_PER_RUN]

    # advance offset for next run
    state["offset"] = offset + len(batch)
    save_state(state)

    return batch, offset


async def process_source(s: dict, sem: asyncio.Semaphore) -> tuple[int, int]:
    """
    Returns (total_processed, new_inserted)
    """
    source_type = s.get("type")
    key = s.get("key")
    company = s.get("company") or key

    async with sem:
        try:
            if source_type == "greenhouse":
                jobs = await fetch_greenhouse(key)
                print(f"Greenhouse {key}: {len(jobs)} jobs")
            elif source_type == "lever":
                jobs = await fetch_lever(key)
                print(f"Lever {key}: {len(jobs)} jobs")
            else:
                return (0, 0)

            total = 0
            new_count = 0

            for j in jobs:
                j["company"] = company
                is_new, _ = upsert_job(j)
                total += 1
                if is_new:
                    new_count += 1

            return (total, new_count)

        except Exception as e:
            print(f"{source_type} {key}: failed -> {e}")
            return (0, 0)


async def main():
    init_db()

    all_sources = load_sources()
    print(f"Loaded sources: {len(all_sources)}")

    if not all_sources:
        print("No sources found. Exiting.")
        return

    batch, offset = select_rotating_batch(all_sources)
    print(f"Crawling batch offset={offset}, size={len(batch)}, concurrency={CONCURRENCY}")

    sem = asyncio.Semaphore(CONCURRENCY)

    # Run sources in parallel (limited by semaphore)
    results = await asyncio.gather(*(process_source(s, sem) for s in batch))

    total_processed = sum(t for t, _ in results)
    new_inserted = sum(n for _, n in results)

    print(f"\nDONE. Total processed: {total_processed}, NEW inserted: {new_inserted}")
    print("Database at: data/jobs.db")


if __name__ == "__main__":
    asyncio.run(main())