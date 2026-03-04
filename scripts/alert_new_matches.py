import json
from pathlib import Path
from app.db.sqlite import get_conn
from app.pipeline.match import match_score
from app.pipeline.alerts import notify

PREFS_PATH = Path("user_prefs.json")
STATE_PATH = Path("data/alert_state.json")

def load_prefs():
    return json.loads(PREFS_PATH.read_text(encoding="utf-8"))

def load_state():
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return {"last_job_id": 0}

def save_state(state):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")

def main():
    prefs = load_prefs()
    state = load_state()
    last_id = int(state.get("last_job_id", 0))

    conn = get_conn()
    cur = conn.cursor()

    # Fetch only NEW jobs since last check
    cur.execute("""
        SELECT id, title, company, location, url, description, first_seen_at
        FROM jobs
        WHERE id > ?
        ORDER BY id ASC
    """, (last_id,))
    rows = cur.fetchall()

    new_last_id = last_id
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
            message=f"{company} | {location}\n{url}\n{reason}"
        )

    state["last_job_id"] = new_last_id
    save_state(state)
    print(f"Checked {len(rows)} new jobs. Matched: {matched}. last_job_id={new_last_id}")

if __name__ == "__main__":
    main()