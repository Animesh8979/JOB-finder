"""Shared HTTP helper for job-source clients.

Uses rotating realistic browser User-Agents and retry logic with exponential
backoff so a single transient failure doesn't silently drop an entire source.
"""
from __future__ import annotations

import random
import time
from datetime import datetime, timezone
from typing import Any

import httpx

# Pool of current, realistic browser UAs (no telltale "bot" strings).
_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.5; rv:133.0) Gecko/20100101 Firefox/133.0",
]

# Default max attempts for transient failures.
DEFAULT_RETRIES = 3
DEFAULT_TIMEOUT = 25.0


def _ua() -> str:
    return random.choice(_USER_AGENTS)


def _is_transient(exc: Exception) -> bool:
    """Return True if the error is likely transient and worth retrying."""
    msg = str(exc).lower()
    return any(
        s in msg
        for s in ("timeout", "timed out", "connect", "read error", "429", "500", "502", "503", "504", "reset")
    )


def get_json(
    url: str,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = DEFAULT_TIMEOUT,
    retries: int = DEFAULT_RETRIES,
) -> Any:
    """GET a URL and return parsed JSON. Retries transient failures with exponential backoff.

    Raises ``httpx.HTTPStatusError`` for non-transient HTTP errors (4xx excluding 429),
    or ``httpx.RequestError`` if all retries are exhausted.
    """
    h = {
        "User-Agent": _ua(),
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
    }
    if headers:
        h.update(headers)

    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            resp = httpx.get(url, params=params, headers=h, timeout=timeout, follow_redirects=True)
            # Retry on 429 / 5xx (transient), raise on other 4xx (client error).
            if resp.status_code == 429 or resp.status_code >= 500:
                last_exc = httpx.HTTPStatusError(
                    f"Server returned {resp.status_code}", request=resp.request, response=resp
                )
                if attempt < retries - 1:
                    _backoff(attempt)
                    continue
                resp.raise_for_status()  # raise the final attempt's error
            resp.raise_for_status()
            return resp.json()
        except httpx.RequestError as e:
            last_exc = e
            if attempt < retries - 1 and _is_transient(e):
                _backoff(attempt)
                continue
            raise
        except httpx.HTTPStatusError as e:
            # Non-transient 4xx — don't retry, just raise.
            if e.response.status_code < 500 and e.response.status_code != 429:
                raise
            last_exc = e
            if attempt < retries - 1:
                _backoff(attempt)
                continue
            raise
    # Should be unreachable, but satisfy the type checker.
    if last_exc:
        raise last_exc
    raise RuntimeError("get_json: exhausted retries with no exception captured")


def post_json(
    url: str,
    json_data: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = DEFAULT_TIMEOUT,
    retries: int = DEFAULT_RETRIES,
) -> Any:
    """POST to a URL with JSON body and return parsed response JSON."""
    h = {
        "User-Agent": _ua(),
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
    }
    if headers:
        h.update(headers)

    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            resp = httpx.post(url, json=json_data or {}, headers=h, timeout=timeout, follow_redirects=True)
            if resp.status_code == 429 or resp.status_code >= 500:
                last_exc = httpx.HTTPStatusError(
                    f"Server returned {resp.status_code}", request=resp.request, response=resp
                )
                if attempt < retries - 1:
                    _backoff(attempt)
                    continue
                resp.raise_for_status()
            resp.raise_for_status()
            return resp.json()
        except httpx.RequestError as e:
            last_exc = e
            if attempt < retries - 1 and _is_transient(e):
                _backoff(attempt)
                continue
            raise
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500 and e.response.status_code != 429:
                raise
            last_exc = e
            if attempt < retries - 1:
                _backoff(attempt)
                continue
            raise
    if last_exc:
        raise last_exc
    raise RuntimeError("post_json: exhausted retries with no exception captured")


def _backoff(attempt: int) -> None:
    """Exponential backoff with jitter: 0.5s, 1s, 2s, 4s... + random jitter."""
    base = 0.5 * (2 ** attempt)
    jitter = random.uniform(0, 0.25)
    time.sleep(base + jitter)


def iso_from_unix(value: Any) -> str:
    """Best-effort convert a unix timestamp (int/str) to an ISO date string."""
    try:
        ts = int(value)
        if ts > 10_000_000_000:  # milliseconds
            ts //= 1000
        return datetime.fromtimestamp(ts, tz=timezone.utc).date().isoformat()
    except Exception:
        return str(value or "")
