"""Common job schema + helpers shared by every source client.

Each source client returns a list of *normalized* job dicts (via ``normalize``) so
the rest of the app never has to care which board a job came from.
"""
from __future__ import annotations

import hashlib
import html
import re
from datetime import datetime
from typing import Any

# The canonical fields a normalized job carries. (Stored in the ``jobs`` table.)
JOB_FIELDS = (
    "dedupe_key", "source", "source_job_id", "title", "company", "location",
    "remote", "url", "apply_url", "description", "salary_min", "salary_max",
    "currency", "tags", "posted_at", "fetched_at", "raw",
)

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"[ \t ]+")
_BLANKLINES_RE = re.compile(r"\n\s*\n\s*\n+")


def strip_html(text: str | None) -> str:
    """Turn an HTML job description into readable plain text."""
    if not text:
        return ""
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</p>", "\n\n", text)
    text = re.sub(r"(?i)<li[^>]*>", "\n• ", text)
    text = _TAG_RE.sub("", text)
    text = html.unescape(text)
    text = _WS_RE.sub(" ", text)
    text = _BLANKLINES_RE.sub("\n\n", text)
    return text.strip()


def make_dedupe_key(source: str, source_job_id: str, title: str, company: str) -> str:
    """Stable key so the same posting isn't stored twice (even across refreshes)."""
    basis = (source_job_id or f"{title}|{company}").lower().strip()
    digest = hashlib.sha1(f"{source}:{basis}".encode("utf-8")).hexdigest()[:16]
    return f"{source}:{digest}"


def normalize(
    *,
    source: str,
    source_job_id: str = "",
    title: str = "",
    company: str = "",
    location: str = "Remote",
    url: str = "",
    apply_url: str = "",
    description: str = "",
    salary_min: int | None = None,
    salary_max: int | None = None,
    currency: str = "",
    tags: list[str] | None = None,
    posted_at: str = "",
    remote: bool = True,
    raw: dict[str, Any] | None = None,
) -> dict[str, Any]:
    title = (title or "").strip()
    company = (company or "").strip()
    return {
        "dedupe_key": make_dedupe_key(source, source_job_id, title, company),
        "source": source,
        "source_job_id": str(source_job_id or ""),
        "title": title,
        "company": company,
        "location": (location or "Remote").strip(),
        "remote": 1 if remote else 0,
        "url": url or apply_url,
        "apply_url": apply_url or url,
        "description": strip_html(description),
        "salary_min": salary_min,
        "salary_max": salary_max,
        "currency": currency,
        "tags": [t for t in (tags or []) if t],
        "posted_at": posted_at,
        "fetched_at": datetime.now().isoformat(timespec="seconds"),
        "raw": raw or {},
    }


def matches_filters(job: dict[str, Any], prefs: dict[str, Any]) -> bool:
    """Pre-filter before the AI scoring step.

    Only the EXCLUDE list rejects a job here. We intentionally do NOT require a title/
    keyword match — that would drop good roles worded differently (e.g. "Engineer" when
    you searched "Developer"). The AI scorer ranks relevance instead, and the score slider
    lets you filter. This maximizes recall while the AI does the precision.
    """
    haystack = f"{job.get('title','')} {job.get('description','')} {' '.join(job.get('tags') or [])}".lower()
    excludes = [w.lower() for w in (prefs.get("exclude") or []) if w]
    if any(w in haystack for w in excludes):
        return False
    return True
