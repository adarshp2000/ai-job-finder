import re
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
from app.db.sqlite import get_conn, utcnow_iso

TRACKING_PARAMS = {"utm_source", "utm_medium", "utm_campaign", "gh_src"}

def canonicalize_url(url: str) -> str:
    u = urlparse(url.strip())
    qs = [(k, v) for k, v in parse_qsl(u.query) if k.lower() not in TRACKING_PARAMS]
    cleaned = u._replace(
        scheme="https",
        netloc=u.netloc.lower(),
        query=urlencode(qs, doseq=True),
        fragment=""
    )
    return urlunparse(cleaned)

def upsert_job(job: dict) -> tuple[bool, int]:
    """
    Returns (is_new, job_id)
    is_new=True if job inserted for the first time.
    """
    conn = get_conn()
    cur = conn.cursor()

    url = job["url"]
    url_c = canonicalize_url(url)
    now = utcnow_iso()

    # try find existing by canonical url
    cur.execute("SELECT id, first_seen_at FROM jobs WHERE url_canonical = ?", (url_c,))
    row = cur.fetchone()

    if row:
        job_id = int(row["id"])
        cur.execute("""
            UPDATE jobs
            SET last_seen_at = ?, title = COALESCE(?, title),
                company = COALESCE(?, company),
                location = COALESCE(?, location),
                description = COALESCE(?, description)
            WHERE id = ?
        """, (
            now,
            job.get("title"),
            job.get("company"),
            job.get("location"),
            job.get("description"),
            job_id
        ))
        conn.commit()
        conn.close()
        return (False, job_id)

    # insert new
    cur.execute("""
        INSERT INTO jobs
        (source, source_key, external_id, url, url_canonical,
         title, company, location, description, first_seen_at, last_seen_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        job.get("source"),
        job.get("source_key"),
        job.get("external_id"),
        url,
        url_c,
        job.get("title"),
        job.get("company"),
        job.get("location"),
        job.get("description"),
        now,
        now
    ))
    job_id = cur.lastrowid
    conn.commit()
    conn.close()
    return (True, int(job_id))