"""Workday deterministic parser — Workday forms are multi-page and JS-heavy."""
from __future__ import annotations

from typing import Any


def fill_workday(page: Any, cfg: dict[str, Any]) -> bool:
    try:
        # Workday's Apply flow is multi-page. We hand off to the hybrid engine,
        # which now includes _paginate_and_fill() for Next-button traversal.
        from src.autofill_runner import _paginate_and_fill
        try:
            page.evaluate("window.scrollTo(0, 0)")
        except Exception:
            pass
        _paginate_and_fill(page, cfg)
    except Exception:
        return False
    return True
