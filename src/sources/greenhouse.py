"""Greenhouse API source integration — direct corporate ATS endpoint."""
from __future__ import annotations

import time
from typing import Any, Optional
from . import base, client
from .adapter_base import SourceAdapter, CancellationToken

SOURCE_ID = "greenhouse"

# Default high-tier tech companies hiring on Greenhouse
DEFAULT_GREENHOUSE_BOARDS = [
    "stripe",
    "figma",
    "cloudflare",
    "datadog",
    "coinbase",
    "discord",
    "pinterest",
    "airbnb",
]


class GreenhouseAdapter(SourceAdapter):
    @property
    def source_id(self) -> str:
        return SOURCE_ID

    def fetch(
        self,
        query: str,
        limit: int,
        prefs: dict[str, Any],
        cancel_token: Optional[CancellationToken] = None,
    ) -> list[dict[str, Any]]:
        return fetch(query, limit, prefs, cancel_token=cancel_token)


def fetch(
    query: str,
    limit: int,
    prefs: dict[str, Any],
    cancel_token: Optional[CancellationToken] = None,
) -> list[dict[str, Any]]:
    """Fetch verified requisitions directly from Greenhouse boards."""
    configured_boards = prefs.get("greenhouse_boards") or []
    boards = configured_boards if configured_boards else DEFAULT_GREENHOUSE_BOARDS

    jobs_out = []
    headers = {"Accept": "application/json"}

    for board in boards:
        if cancel_token and cancel_token.is_cancelled():
            break

        if jobs_out:
            time.sleep(0.5)

        # Include ?content=true to get full descriptions in a single round-trip
        url = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true"
        try:
            resp = client.get_json(url, headers=headers)
            if not resp or "jobs" not in resp:
                continue

            for j in resp["jobs"]:
                if cancel_token and cancel_token.is_cancelled():
                    break
                title = j.get("title", "")
                if query and query.lower() not in title.lower():
                    continue

                loc = j.get("location", {}).get("name", "")
                remote = bool(
                    "remote" in (loc or "").lower()
                    or "anywhere" in (loc or "").lower()
                    or "remote" in title.lower()
                )

                # Clean content description
                desc_html = j.get("content") or ""
                from .base import strip_html
                description = strip_html(desc_html) if desc_html else ""

                normalized_job = base.normalize(
                    source=SOURCE_ID,
                    source_job_id=str(j.get("internal_job_id") or j.get("id", "")),
                    title=title,
                    company=board.replace("-", " ").title(),
                    location=loc or "Remote",
                    url=j.get("absolute_url", ""),
                    apply_url=j.get("absolute_url", ""),
                    description=description,
                    tags=[j.get("department", "")] if j.get("department") else [],
                    posted_at=j.get("updated_at", ""),
                    remote=remote,
                    raw=j,
                )
                jobs_out.append(normalized_job)
                if len(jobs_out) >= limit:
                    return jobs_out

        except Exception:
            # Gracefully handle single board failures
            continue

    return jobs_out
