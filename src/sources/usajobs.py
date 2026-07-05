"""USAJobs official API (requires API key from data.usajobs.gov).

Documents: https://developer.usajobs.gov/
"""
from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

from . import base
from .client import get_json

SOURCE_ID = "usajobs"
ENDPOINT = "https://data.usajobs.gov/api/search"


def fetch(query: str, limit: int, prefs: dict[str, Any]) -> list[dict[str, Any]]:
    api_key = (prefs.get("usajobs_api_key") or "").strip()
    email = (prefs.get("usajobs_email") or "").strip()
    if not api_key or not email:
        return []  # silently skip; user hasn't set a USAJobs key
    keywords = (prefs.get("keywords") or [""])
    payload = {
        "Keyword": " ".join(keywords[:3]).strip() or query or "remote",
        "ResultsPerPage": str(min(limit, 50)),
    }
    url = f"{ENDPOINT}?{urlencode(payload)}"
    headers = {
        "Host": "data.usajobs.gov",
        "User-Agent": email,
        "Authorization-Key": api_key,
    }
    try:
        data = get_json(url, headers=headers)
    except Exception:
        return []
    out: list[dict[str, Any]] = []
    for j in ((data or {}).get("SearchResult") or {}).get("SearchResultItems") or []:
        if not isinstance(j, dict):
            continue
        details = j.get("MatchedObjectDescriptor") or {}
        url_v = details.get("PositionURI") or ""
        out.append(
            base.normalize(
                source=SOURCE_ID,
                source_job_id=str(details.get("PositionID") or ""),
                title=details.get("PositionTitle") or "",
                company=(details.get("OrganizationName") or ""),
                location=(details.get("PositionLocationDisplay") or "Remote"),
                url=url_v,
                apply_url=url_v,
                description=details.get("UserArea") or "",
                salary_min=_sal(details.get("PositionRemuneration"), "MinimumRange"),
                salary_max=_sal(details.get("PositionRemuneration"), "MaximumRange"),
                posted_at=details.get("PublicationStartDate") or "",
                raw=details,
            )
        )
        if len(out) >= limit:
            break
    return out


def _sal(rem: Any, key: str) -> int | None:
    try:
        v = ((rem or [{}])[0] or {}).get(key)
        return int(float(str(v).replace(",", ""))) if v else None
    except Exception:
        return None
