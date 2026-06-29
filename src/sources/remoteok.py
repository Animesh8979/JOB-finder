"""RemoteOK — free public API. https://remoteok.com/api  (first item is metadata)."""
from __future__ import annotations

from typing import Any

from . import base
from .client import get_json, iso_from_unix

SOURCE_ID = "remoteok"
ENDPOINT = "https://remoteok.com/api"


def fetch(query: str, limit: int, prefs: dict[str, Any]) -> list[dict[str, Any]]:
    data = get_json(ENDPOINT)
    if not isinstance(data, list):
        return []
    out = []
    for j in data:
        # The legal/notice element has no "position"/"id" job fields.
        if not isinstance(j, dict) or not (j.get("position") or j.get("id")):
            continue
        url = j.get("url") or (f"https://remoteok.com/remote-jobs/{j.get('slug','')}" if j.get("slug") else "")
        out.append(
            base.normalize(
                source=SOURCE_ID,
                source_job_id=str(j.get("id", "")),
                title=j.get("position", ""),
                company=j.get("company", ""),
                location=j.get("location") or "Remote",
                url=url,
                apply_url=j.get("apply_url") or url,
                description=j.get("description", ""),
                tags=j.get("tags") or [],
                salary_min=j.get("salary_min") or None,
                salary_max=j.get("salary_max") or None,
                currency="USD" if j.get("salary_min") else "",
                posted_at=iso_from_unix(j.get("epoch")) if j.get("epoch") else j.get("date", ""),
                raw=j,
            )
        )
        if len(out) >= limit:
            break
    return out
