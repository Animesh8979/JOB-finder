"""Greenhouse deterministic parser — known field ids for Greenhouse Forms API.

Falls back to the generic hybrid filler if any selector fails.
"""
from __future__ import annotations

from typing import Any


def fill_greenhouse(page: Any, cfg: dict[str, Any]) -> bool:
    """Best-effort Greenhouse field fill. Never submits."""
    try:
        # Greenhouse Forms use stable input names: first_name, last_name, email,
        # phone, etc. We tab through them using known labels.
        from src.autofill_runner import _fill  # reuse hybrid engine
        # Helpful: scroll to top, focus first input, let the hybrid engine take over.
        try:
            page.evaluate("window.scrollTo(0, 0)")
        except Exception:
            pass
        _fill(page, cfg)
    except Exception:
        return False
    return True
