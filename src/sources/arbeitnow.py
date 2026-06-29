"""Arbeitnow — free public job-board API. https://www.arbeitnow.com/api/job-board-api"""
from __future__ import annotations

from typing import Any

from . import base
from .client import get_json, iso_from_unix

SOURCE_ID = "arbeitnow"
ENDPOINT = "https://www.arbeitnow.com/api/job-board-api"


def fetch(query: str, limit: int, prefs: dict[str, Any]) -> list[dict[str, Any]]:
    data = get_json(ENDPOINT)
    rows = data.get("data", []) if isinstance(data, dict) else []
    out = []
    for j in rows[:limit]:
        out.append(
            base.normalize(
                source=SOURCE_ID,
                source_job_id=str(j.get("slug", "")),
                title=j.get("title", ""),
                company=j.get("company_name", ""),
                location=j.get("location") or "Remote",
                url=j.get("url", ""),
                apply_url=j.get("url", ""),
                description=j.get("description", ""),
                tags=(j.get("tags") or []) + (j.get("job_types") or []),
                posted_at=iso_from_unix(j.get("created_at")) if j.get("created_at") else "",
                remote=bool(j.get("remote", True)),
                raw=j,
            )
        )
    return out
