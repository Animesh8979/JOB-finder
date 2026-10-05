"""Lever API source integration — direct unauthenticated corporate postings."""
from __future__ import annotations

import time
from typing import Any, Optional
from . import base, client
from .adapter_base import SourceAdapter, CancellationToken

SOURCE_ID = "lever"

# Default tech organizations hiring on Lever
DEFAULT_LEVER_BOARDS = [
    "spotify",
    "atlassian",
    "palantir",
    "affirm",
    "coupa",
]


class LeverAdapter(SourceAdapter):
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
    """Fetch verified requisitions directly from Lever API."""
    configured_boards = prefs.get("lever_boards") or []
    boards = configured_boards if configured_boards else DEFAULT_LEVER_BOARDS

    jobs_out = []

    for board in boards:
        if cancel_token and cancel_token.is_cancelled():
            break

        if jobs_out:
            time.sleep(0.5)

        url = f"https://api.lever.co/v0/postings/{board}?mode=json"
        try:
            resp = client.get_json(url)
            if not resp or not isinstance(resp, list):
                continue

            for j in resp:
                if cancel_token and cancel_token.is_cancelled():
                    break
                title = j.get("text", "")
                if query and query.lower() not in title.lower():
                    continue

                cats = j.get("categories") or {}
                loc = cats.get("location") or ""
                commitment = cats.get("commitment") or ""
                team = cats.get("team") or ""
                workplace_type = cats.get("workplaceType") or ""

                remote = bool(
                    "remote" in (loc or "").lower()
                    or "anywhere" in (loc or "").lower()
                    or "remote" in title.lower()
                    or "remote" in workplace_type.lower()
                )

                description = j.get("descriptionPlain") or ""

                normalized_job = base.normalize(
                    source=SOURCE_ID,
                    source_job_id=str(j.get("id", "")),
                    title=title,
                    company=board.replace("-", " ").title(),
                    location=loc or "Remote",
                    url=j.get("hostedUrl", ""),
                    apply_url=j.get("applyUrl") or j.get("hostedUrl", ""),
                    description=description,
                    tags=[t for t in [team, commitment] if t],
                    posted_at=client.iso_from_unix(j.get("createdAt")) if j.get("createdAt") else "",
                    remote=remote,
                    raw=j,
                )
                jobs_out.append(normalized_job)
                if len(jobs_out) >= limit:
                    return jobs_out

        except Exception as e:
            continue

    return jobs_out
