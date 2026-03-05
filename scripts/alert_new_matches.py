import json
from pathlib import Path

from app.db.sqlite import get_conn
from app.pipeline.match import match_score
from app.pipeline.alerts import notify

PREFS_PATH = Path("user_prefs.json")
STATE_PATH = Path("data/alert_state.json")

MAX_ALERTS = 10


def load_prefs():
    if not PREFS_PATH.exists():
        print("user_prefs.json not found.")
        return {}
    return json.loads(PREFS_PATH.read_text(encoding="utf-8"))


def load_state():
    if not STATE_PATH.exists():
        return {"last_job_id": 0}

    txt = STATE_PATH.read_text(encoding="utf-8").strip()
    if not txt:
        return {"last_job_id": 0}

    try:
        return json.loads(txt)
    except json.JSONDecodeError:
        return {"last_job_id": 0}


def save_state(state: dict):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")


def main():
    prefs = load_prefs()
    state = load_state()

    last_job_id = int(state.get("last_job_id", 0))
    new_last_id = last_job_id

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, title, company, location, url, description, first_seen_at
        FROM jobs
        WHERE id > ?
        ORDER BY id ASC
        """,
        (last_job_id,),
    )

    rows = cur.fetchall()

    matched = 0

    for r in rows:
        job = dict(r)

        is_match, score, reason = match_score(job, prefs)

        new_last_id = max(new_last_id, job["id"])

        if not is_match:
            continue

        matched += 1

        title = job.get("title") or "New Job"
        company = job.get("company") or ""
        location = job.get("location") or ""
        url = job.get("url") or ""

        notify(
            title=f"NEW MATCH ({score:.2f}) - {title}",
            message=f"{company} | {location}\n{url}\n{reason}",
        )

        if matched >= MAX_ALERTS:
            break

    save_state({"last_job_id": new_last_id})
    print(f"Checked {len(rows)} new jobs. Matched: {matched}. last_job_id={new_last_id}")


if __name__ == "__main__":
    main()