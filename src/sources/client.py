"""Shared HTTP helper for job-source clients (polite UA, timeouts, JSON)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx

USER_AGENT = (
    "RemoteJobApplicationCopilot/1.0 (personal job search tool; contact: local user)"
)
DEFAULT_TIMEOUT = 25.0


def get_json(
    url: str,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> Any:
    h = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if headers:
        h.update(headers)
    resp = httpx.get(url, params=params, headers=h, timeout=timeout, follow_redirects=True)
    resp.raise_for_status()
    return resp.json()


def iso_from_unix(value: Any) -> str:
    """Best-effort convert a unix timestamp (int/str) to an ISO date string."""
    try:
        ts = int(value)
        if ts > 10_000_000_000:  # milliseconds
            ts //= 1000
        return datetime.fromtimestamp(ts, tz=timezone.utc).date().isoformat()
    except Exception:
        return str(value or "")
