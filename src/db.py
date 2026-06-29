"""SQLite storage for jobs, applications, recruiter contacts, and outreach logs.

Uses sqlite3. Returns plain dicts so the Streamlit pages don't need to know about db internals.
"""
from __future__ import annotations

import json
import sqlite3
import time
import random
import threading
from datetime import date, datetime
from typing import Any, Iterable

from . import config

# Application lifecycle statuses (shown in the Tracker).
STATUSES = [
    "Saved",
    "Tailored",
    "Applied",
    "Followed-up",
    "Interview",
    "Offer",
    "Closed",
    "Rejected",
]


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")

_local = threading.local()

class _CursorManager:
    def __init__(self, row_factory=None):
        if not hasattr(_local, "conn"):
            # We enforce auto-commit behavior (isolation_level=None) to manage transactions manually
            _local.conn = sqlite3.connect(config.DB_PATH, timeout=10.0, isolation_level=None)
            # Strict mitigations for concurrency
            _local.conn.execute("PRAGMA journal_mode=WAL;")
            _local.conn.execute("PRAGMA synchronous=NORMAL;")
            _local.conn.execute("PRAGMA busy_timeout=5000;")
            
        self.conn = _local.conn
        self.row_factory = row_factory

    def __enter__(self):
        if self.row_factory:
            self.conn.row_factory = self.row_factory
        else:
            self.conn.row_factory = None
            
        self.cur = self.conn.cursor()
        # Application-level backoff mitigation
        retries = 10
        for i in range(retries):
            try:
                self.cur.execute("BEGIN IMMEDIATE")
                break
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and i < retries - 1:
                    time.sleep(random.uniform(0.05, 0.2))
                else:
                    raise e
        return self.cur

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.cur.execute("COMMIT")
        else:
            self.cur.execute("ROLLBACK")
        self.cur.close()
        # Do not close connection to maintain thread-local pool

def get_conn():
    return _CursorManager()

def init_db() -> None:
    """Create tables if they do not exist. Safe to call on every launch."""
    with _CursorManager() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                dedupe_key    TEXT UNIQUE,
                source        TEXT,
                source_job_id TEXT,
                title         TEXT,
                company       TEXT,
                location      TEXT,
                remote        INTEGER DEFAULT 1,
                url           TEXT,
                apply_url     TEXT,
                description   TEXT,
                salary_min    INTEGER,
                salary_max    INTEGER,
                currency      TEXT,
                tags          TEXT,
                posted_at     TEXT,
                fetched_at    TEXT,
                raw           TEXT,
                match_score   INTEGER,
                match_reason  TEXT,
                scored_at     TEXT
            );
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS applications (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id              INTEGER UNIQUE REFERENCES jobs(id) ON DELETE CASCADE,
                status              TEXT DEFAULT 'Saved',
                tailored_resume_text TEXT,
                cover_letter_text   TEXT,
                tailored_resume_path TEXT,
                cover_letter_path   TEXT,
                applied_at          TEXT,
                follow_up_at        TEXT,
                notes               TEXT,
                created_at          TEXT,
                updated_at          TEXT
            );
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS contacts (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT,
                email      TEXT UNIQUE,
                company    TEXT,
                role       TEXT,
                source     TEXT,
                notes      TEXT,
                job_id     INTEGER REFERENCES jobs(id) ON DELETE SET NULL,
                created_at TEXT
            );
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS outreach_log (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_id INTEGER REFERENCES contacts(id) ON DELETE SET NULL,
                job_id     INTEGER REFERENCES jobs(id) ON DELETE SET NULL,
                subject    TEXT,
                body       TEXT,
                channel    TEXT,
                status     TEXT,
                created_at TEXT,
                sent_at    TEXT
            );
            """
        )
        cur.execute("CREATE INDEX IF NOT EXISTS idx_jobs_score ON jobs(match_score);")


# --- Row helpers -------------------------------------------------------------
def _row_to_dict(row) -> dict[str, Any] | None:
    if row is None:
        return None
    d = dict(row)
    for k in ("tags", "raw"):
        if k in d and isinstance(d[k], str) and d[k]:
            try:
                d[k] = json.loads(d[k])
            except Exception:
                pass
    return d


def _rows(cur: Iterable) -> list[dict[str, Any]]:
    return [d for d in (_row_to_dict(r) for r in cur) if d is not None]


# --- Jobs --------------------------------------------------------------------
def upsert_job(job: dict[str, Any]) -> int:
    """Insert a normalized job (dict). If the dedupe_key already exists, keep the
    existing row and return its id. Returns the job id."""
    with _CursorManager(row_factory=sqlite3.Row) as cur:
        insert_data = {
            "source": "",
            "source_job_id": "",
            "title": "",
            "company": "",
            "location": "",
            "remote": 1,
            "url": "",
            "apply_url": "",
            "description": "",
            "salary_min": None,
            "salary_max": None,
            "currency": "",
            "posted_at": None,
            **job,
            "tags": json.dumps(job.get("tags") or []),
            "raw": json.dumps(job.get("raw") or {}, ensure_ascii=False),
            "fetched_at": job.get("fetched_at") or _now(),
        }
        
        cur.execute(
            """
            INSERT INTO jobs (dedupe_key, source, source_job_id, title, company,
                location, remote, url, apply_url, description, salary_min, salary_max,
                currency, tags, posted_at, fetched_at, raw)
            VALUES (:dedupe_key, :source, :source_job_id, :title, :company, :location,
                :remote, :url, :apply_url, :description, :salary_min, :salary_max,
                :currency, :tags, :posted_at, :fetched_at, :raw)
            ON CONFLICT (dedupe_key) DO UPDATE SET fetched_at = EXCLUDED.fetched_at
            RETURNING id
            """,
            insert_data,
        )
        return int(cur.fetchone()["id"])


def set_job_score(job_id: int, score: int, reason: str) -> None:
    with _CursorManager() as cur:
        cur.execute(
            "UPDATE jobs SET match_score = ?, match_reason = ?, scored_at = ? WHERE id = ?",
            (int(score), reason, _now(), job_id),
        )


def get_job(job_id: int) -> dict[str, Any] | None:
    with _CursorManager(row_factory=sqlite3.Row) as cur:
        cur.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
        return _row_to_dict(cur.fetchone())


def list_jobs(
    only_scored: bool = False,
    min_score: int = 0,
    search: str = "",
    order_by_score: bool = True,
    limit: int = 500,
) -> list[dict[str, Any]]:
    q = "SELECT * FROM jobs WHERE 1=1"
    params: list[Any] = []
    if only_scored:
        q += " AND match_score IS NOT NULL"
    if min_score:
        q += " AND COALESCE(match_score, 0) >= ?"
        params.append(min_score)
    if search:
        q += " AND (title LIKE ? OR company LIKE ? OR description LIKE ?)"
        like = f"%{search}%"
        params += [like, like, like]
    q += " ORDER BY " + (
        "COALESCE(match_score, -1) DESC, id DESC" if order_by_score else "id DESC"
    )
    q += " LIMIT ?"
    params.append(limit)
    with _CursorManager(row_factory=sqlite3.Row) as cur:
        cur.execute(q, tuple(params))
        return _rows(cur.fetchall())


def unscored_jobs(limit: int = 100) -> list[dict[str, Any]]:
    with _CursorManager(row_factory=sqlite3.Row) as cur:
        cur.execute(
            "SELECT * FROM jobs WHERE match_score IS NULL ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        return _rows(cur.fetchall())


# --- Applications ------------------------------------------------------------
def get_or_create_application(job_id: int) -> dict[str, Any]:
    with _CursorManager(row_factory=sqlite3.Row) as cur:
        cur.execute("SELECT * FROM applications WHERE job_id = ?", (job_id,))
        row = cur.fetchone()
        if row:
            return dict(row)
        now = _now()
        cur.execute(
            "INSERT INTO applications (job_id, status, created_at, updated_at) "
            "VALUES (?, 'Saved', ?, ?)",
            (job_id, now, now),
        )
        cur.execute("SELECT * FROM applications WHERE job_id = ?", (job_id,))
        return dict(cur.fetchone())


def get_application(job_id: int) -> dict[str, Any] | None:
    with _CursorManager(row_factory=sqlite3.Row) as cur:
        cur.execute("SELECT * FROM applications WHERE job_id = ?", (job_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def update_application(job_id: int, **fields: Any) -> None:
    ALLOWED_COLS = {"status", "tailored_resume_text", "cover_letter_text", "tailored_resume_path", "cover_letter_path", "applied_at", "follow_up_at", "notes", "created_at", "updated_at"}
    fields = {k: v for k, v in fields.items() if k in ALLOWED_COLS}
    if not fields:
        return
    fields["updated_at"] = _now()
    sets = ", ".join(f"{k} = ?" for k in fields)
    with _CursorManager() as cur:
        # Atomic upsert
        cur.execute("SELECT id FROM applications WHERE job_id = ?", (job_id,))
        if not cur.fetchone():
            now = _now()
            cur.execute(
                "INSERT INTO applications (job_id, status, created_at, updated_at) "
                "VALUES (?, 'Saved', ?, ?)",
                (job_id, now, now),
            )
        cur.execute(
            f"UPDATE applications SET {sets} WHERE job_id = ?",
            (*fields.values(), job_id),
        )


def list_applications() -> list[dict[str, Any]]:
    """Applications joined to their job, for the Tracker page."""
    with _CursorManager(row_factory=sqlite3.Row) as cur:
        cur.execute(
            """
            SELECT a.*, j.title, j.company, j.url, j.apply_url, j.match_score
            FROM applications a JOIN jobs j ON j.id = a.job_id
            ORDER BY a.updated_at DESC
            """
        )
        return [dict(r) for r in cur.fetchall()]


# --- Contacts ----------------------------------------------------------------
def add_contact(**fields: Any) -> int:
    ALLOWED_COLS = {"name", "email", "company", "role", "source", "notes", "job_id", "created_at"}
    fields = {k: v for k, v in fields.items() if k in ALLOWED_COLS}
    fields.setdefault("created_at", _now())
    cols = ", ".join(fields.keys())
    placeholders = ", ".join(f":{k}" for k in fields.keys())
    with _CursorManager(row_factory=sqlite3.Row) as cur:
        if fields.get("email"):
            cur.execute("SELECT id FROM contacts WHERE email = :email", {"email": fields["email"]})
            existing = cur.fetchone()
            if existing:
                return int(existing["id"])
        
        cur.execute(
            f"INSERT INTO contacts ({cols}) VALUES ({placeholders}) RETURNING id", fields
        )
        return int(cur.fetchone()["id"])


def list_contacts() -> list[dict[str, Any]]:
    with _CursorManager(row_factory=sqlite3.Row) as cur:
        cur.execute("SELECT * FROM contacts ORDER BY id DESC")
        return [dict(r) for r in cur.fetchall()]


def get_contact(contact_id: int) -> dict[str, Any] | None:
    with _CursorManager(row_factory=sqlite3.Row) as cur:
        cur.execute("SELECT * FROM contacts WHERE id = ?", (contact_id,))
        row = cur.fetchone()
        return dict(row) if row else None


# --- Outreach ----------------------------------------------------------------
def add_outreach(**fields: Any) -> int:
    ALLOWED_COLS = {"contact_id", "job_id", "subject", "body", "channel", "status", "created_at", "sent_at"}
    fields = {k: v for k, v in fields.items() if k in ALLOWED_COLS}
    fields.setdefault("created_at", _now())
    fields.setdefault("status", "draft")
    cols = ", ".join(fields.keys())
    placeholders = ", ".join(f":{k}" for k in fields.keys())
    with _CursorManager(row_factory=sqlite3.Row) as cur:
        cur.execute(
            f"INSERT INTO outreach_log ({cols}) VALUES ({placeholders}) RETURNING id", fields
        )
        return int(cur.fetchone()["id"])


def count_outreach_today() -> int:
    today = date.today().isoformat()
    with _CursorManager(row_factory=sqlite3.Row) as cur:
        cur.execute(
            "SELECT COUNT(*) AS n FROM outreach_log WHERE substr(created_at, 1, 10) = ?",
            (today,),
        )
        row = cur.fetchone()
        return int(row["n"])


def list_outreach() -> list[dict[str, Any]]:
    with _CursorManager(row_factory=sqlite3.Row) as cur:
        cur.execute(
            """
            SELECT o.*, c.name AS contact_name, c.email AS contact_email
            FROM outreach_log o LEFT JOIN contacts c ON c.id = o.contact_id
            ORDER BY o.id DESC
            """
        )
        return [dict(r) for r in cur.fetchall()]

def application_stats() -> dict:
    """Return funnel statistics."""
    stats = {}
    with _CursorManager() as cur:
        cur.execute("SELECT COUNT(*) FROM applications WHERE status='Saved'")
        stats["total_saved"] = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM applications WHERE status='Tailored'")
        stats["total_tailored"] = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM applications WHERE status='Applied'")
        stats["total_applied"] = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM applications WHERE status='Interview'")
        stats["total_interview"] = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM applications WHERE status='Offer'")
        stats["total_offer"] = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM applications WHERE status='Rejected'")
        stats["total_rejected"] = cur.fetchone()[0]
        
        # average score
        cur.execute("SELECT AVG(match_score) FROM jobs j JOIN applications a ON j.id = a.job_id")
        avg_score_row = cur.fetchone()
        stats["avg_score"] = round(avg_score_row[0], 1) if avg_score_row and avg_score_row[0] else 0.0
        
        # response rate
        total_responses = stats["total_interview"] + stats["total_offer"] + stats["total_rejected"]
        total_outreach = stats["total_applied"] + total_responses
        stats["response_rate"] = round((total_responses / total_outreach * 100), 1) if total_outreach > 0 else 0.0
        
        # best source
        cur.execute('''
            SELECT source, COUNT(*) as c FROM jobs j 
            JOIN applications a ON j.id = a.job_id 
            WHERE a.status IN ('Interview', 'Offer') 
            GROUP BY source ORDER BY c DESC LIMIT 1
        ''')
        best_source_row = cur.fetchone()
        stats["best_source"] = best_source_row[0] if best_source_row else "None yet"
        
    return stats

# --- Semantic Vector Search (ChromaDB) ---------------------------------------
_chroma_client = None

def get_chroma():
    global _chroma_client
    if _chroma_client is None:
        try:
            import chromadb
            from . import config
            chroma_dir = config.DATA_DIR / "chroma"
            chroma_dir.mkdir(parents=True, exist_ok=True)
            _chroma_client = chromadb.PersistentClient(path=str(chroma_dir))
        except ImportError:
            _chroma_client = False  # Mark as unavailable
    return _chroma_client

def upsert_job_embedding(job_id: int, text: str) -> None:
    client = get_chroma()
    if client:
        col = client.get_or_create_collection("jobs")
        col.upsert(ids=[str(job_id)], documents=[text])

def search_similar_jobs(query: str, n_results: int = 5) -> list[str]:
    client = get_chroma()
    if client:
        col = client.get_or_create_collection("jobs")
        res = col.query(query_texts=[query], n_results=n_results)
        return res["ids"][0] if res["ids"] else []
    return []
