from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List

from api.db import get_db
import api.schemas
from app.pipeline.match import match_score
import json
from pathlib import Path

app = FastAPI(title="AI Job Finder API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/jobs", response_model=List[api.schemas.JobOut])
def list_jobs(
    q: Optional[str] = Query(None),
    company: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    limit: int = Query(50),
    offset: int = Query(0),
):
    conn = get_db()
    cur = conn.cursor()

    where = []
    params = []

    if q:
        where.append("(title LIKE ? OR description LIKE ?)")
        params.extend([f"%{q}%", f"%{q}%"])

    if company:
        where.append("company LIKE ?")
        params.append(f"%{company}%")

    if location:
        where.append("location LIKE ?")
        params.append(f"%{location}%")

    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    cur.execute(
        f"""
        SELECT id, title, company, location, url, description, first_seen_at
        FROM jobs
        {where_sql}
        ORDER BY id DESC
        LIMIT ? OFFSET ?
        """,
        (*params, limit, offset),
    )

    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

PREFS_PATH = Path("user_prefs.json")

def load_prefs():
    if not PREFS_PATH.exists():
        return {}
    return json.loads(PREFS_PATH.read_text(encoding="utf-8"))

@app.get("/matches")
def matches(limit: int = 50, offset: int = 0):
    prefs = load_prefs()

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, title, company, location, url, description, first_seen_at
        FROM jobs
        ORDER BY id DESC
        LIMIT 500
        """
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()

    scored = []
    for job in rows:
        ok, score, reason = match_score(job, prefs)
        if ok:
            scored.append({
                **job,
                "score": float(score),
                "reason": reason
            })

    scored.sort(key=lambda x: x["score"], reverse=True)

    return scored[offset: offset + limit]